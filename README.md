# Pegasus

**Behavioral File-System Telemetry, Containment & Recovery Agent (Prototype v1)**

Pegasus is a **user-space Linux endpoint agent** that observes filesystem activity in real time, classifies behavioral intent, and performs automated containment and recovery using versioned snapshots and optional off-site encrypted backups.

The system is **behavior-driven**, not signature-based.

---

## High-Level Flow

1. System startup and cryptographic initialization
2. Concurrent worker threads initialized
3. Real-time filesystem observation
4. Stability-aware snapshot scheduling
5. Time-windowed behavioral intent classification
6. Escalation to containment on critical state
7. Automated restore and optional off-site backup

---

## Cryptographic Initialization & Off-Site Backup Design

On startup, Pegasus prompts the user for a **passkey**.

This passkey is used to derive encryption keys for **off-site backup uploads**.

Key characteristics:

* A **random salt** is generated at runtime on each start
* The salt is stored locally in a binary, non-human-readable file (`crypto.txt`)
* Encryption is performed **in memory**
* Only encrypted data is ever transmitted off-host

This design establishes the foundation for a **future two-way off-site backup pipeline**, enabling restore from cloud storage in later versions.
Version v1 implements **one-way encrypted uploads only**.

---

## Core Architecture

Pegasus operates as a **multi-threaded daemon**, with explicitly separated responsibilities.

---

## Worker Threads (I/O & Persistence)

### File Thread

Handles filesystem operations requested by the scheduler:

* snapshot creation
* file reads
* restore writes
* cleanup actions

Operations are serialized through an internal task queue to avoid direct contention.

---

### Database Thread

Handles all persistence operations using **SQLite**:

* snapshot metadata
* version flags
* lifecycle state

Database access is isolated to this thread to maintain consistency.

---

## Filesystem Observation & Snapshot Scheduling

### Observer Thread

* Monitors a **single root directory** (scope choice for v1)
* Recursively observes all subdirectories and files
* Captures:

  * create / modify / delete / rename events
  * timestamps
  * rename metadata

The observer populates shared in-memory structures:

* a **file dictionary** (live file state)
* a **heap** (scheduled snapshot candidates)

---

### Scheduler Thread

* Consumes entries from the heap
* Applies a **stability window** to avoid mid-write snapshotting
* Validates heap entries against the file dictionary to discard stale events
* Dispatches snapshot tasks to the file thread

This pipeline approximates **real-time snapshotting** without relying on filesystem journaling.

---

## Version Lifecycle Management

### Version Controller Thread

* Periodically evaluates snapshot age and relevance
* Updates database flags indicating whether versions are safe to delete

---

### File Auditor Thread

* Reads version flags from the database
* Performs asynchronous physical deletion of obsolete snapshots

This decouples **logical versioning** from **physical cleanup**.

---

## Behavioral Detection Pipeline

### Intent Classifier Thread

The intent classifier runs periodically using **time-windowed analysis**.

It consumes snapshots of the file dictionary and evaluates behavior using multiple detectors, including:

* burst modification frequency
* inter-event timing deltas
* entropy delta (relative change)
* ASCII ratio fallback for unknown formats
* rename and extension mutation detection
* directory-level multi-file correlation

Classification occurs across three layers:

* per-file intent scoring
* directory aggregation
* global system state machine:

  * `SAFE`
  * `WARNING`
  * `CRITICAL`

State de-escalation occurs automatically after sustained quiet periods.

---

## Containment & Escalation

When `CRITICAL` is reached, the intent classifier signals containment.

### Process Monitor Thread

* Attempts best-effort attribution and termination using process heuristics
* Uses filesystem context and runtime metadata

### Fallback Containment

If reliable termination is not possible, Pegasus enforces **directory locking** to prevent further damage.

Containment prioritizes **damage limitation**, not perfect attribution.

---

## Snapshot Invariants & Recovery Semantics

Pegasus enforces strict snapshot rules based on system state:

* **SAFE**

  * snapshots taken normally
* **WARNING**

  * snapshots taken but flagged as *potentially compromised*
* **CRITICAL**

  * snapshotting stops immediately

---

### Restore Behavior

On `CRITICAL`, Pegasus initiates automated recovery:

* restores from available snapshot history
* restored files are written with **stale-identifying suffixes**
  (e.g. `report.txt.restored_v2`, `image.png.recovered_1705439210`)
* restored data is **bit-correct relative to the snapshot**
* restored content may be semantically stale but internally consistent

No overwrite occurs without traceability.

---

## Off-Site Encrypted Backup (Required)

Pegasus integrates off-site encrypted backups into the **core recovery pipeline** using Google Cloud Storage.

On startup, the system derives encryption material from a user-provided passkey and performs **automatic one-way encrypted uploads** to a configured GCS bucket during escalation and recovery.

### Contract

Pegasus requires the following to exist prior to runtime:

* A Google Cloud Storage bucket
* Credentials with write access to the bucket
* Environment variables configured for authentication

**.env.example**
GOOGLE_APPLICATION_CREDENTIALS= #your .json file provided for this project
CLIENT_BUCKET= #reference to your bucket in GCS for the given project

Encryption is performed **in memory** before transmission.
Only encrypted objects are written to cloud storage.

### Failure Semantics

If cloud configuration is missing or invalid:

* Pegasus fails during recovery initialization
* Local detection and snapshotting may continue
* Automated recovery is unavailable

Pegasus does not provision cloud resources or manage IAM configuration.

---

## Known Limitations

### User-Space Enforcement

* Process attribution and termination are best-effort
* Short-lived or forked processes may evade containment
* Kernel-level enforcement is out of scope

---

### Temporal Classification Lag

* Intent detection occurs after a time window
* Some snapshots may predate escalation
* Restored data may not represent the most recent semantic version

---

### Shutdown Semantics

* Some threads may block on waits
* Unified shutdown coordination is incomplete
* Forced termination may interrupt background tasks

---

### Shared State Coupling

* Central shared structures increase coupling
* Message-passing refactors are deferred to later versions

---

## Scope & Non-Goals

Pegasus is not:

* a kernel-level EDR
* a signature-based scanner
* a guaranteed process killer
* production-hardened security software

Pegasus is:

* a behavioral detection prototype
* a recovery-aware defensive agent
* a systems-engineering exploration

---

## Project Status

* Prototype (v1)
* Feature-complete for intended scope
* Suitable for freeze and evaluation

---

## Installation

Pegasus is designed to run on **Linux** as a user-space daemon.

### Requirements

* Linux (tested on modern distributions)
* Python 3.10+
* POSIX filesystem with inotify support
* SQLite 3 (local file-based database)
* Sufficient permissions to:

  * observe filesystem events
  * read/write monitored directories
  * attempt best-effort process inspection

---

### Setup

Clone the repository:

```bash
git clone https://github.com/sohamdawn777/pegasus.git
cd pegasus
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---



### Running Pegasus

Start the agent:

```bash
python -m backend.main
```

Pegasus runs as a long-lived process and begins monitoring immediately after startup.

Logs and state transitions are emitted continuously during runtime.

---

### Stopping the Agent

Terminate the process manually (e.g. `Ctrl+C` or signal-based stop).

Note:

* Some background workers may block briefly during shutdown
* Forced termination may interrupt cleanup tasks

This behavior is expected for the current prototype version.

---

### Deployment Notes

* Pegasus is intended to be run in **controlled environments**
* Running as a privileged user may improve visibility but is not required
* Kernel-level enforcement is outside the scope of this version

---

### Simulating Attacks

To generate controlled destructive filesystem activity for testing, activate the same virtual environment (venv) in a **separate terminal** and run the simulation script while Pegasus is active:

```bash
python -m simulation.test_script
```

The simulation produces high-frequency file modifications, renames, and entropy shifts designed to trigger behavioral escalation and recovery flows.

This script is intended **only for local testing and demonstration**.

---

## Future Work

* Snapshot quarantine and retroactive invalidation
* Cleaner shutdown coordination
* Reduced shared-state coupling
* Two-way offsite backup pipeline (Google Cloud Storage)
* Optional kernel-level extensions (out of scope for v1)

---

## License

MIT

---

## Author

Soham Dawn
Backend Systems & Security-Oriented Engineering

---

### Closing

Pegasus prioritizes **behavior, time, and recovery**—the most fundamental aspects of defensive systems.

Its limitations are explicit, bounded, and understood.

---