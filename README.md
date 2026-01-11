# Pegasus

**Behavioral File-System Telemetry, Containment & Recovery Agent (Prototype v1)**

Pegasus is a **user-space Linux endpoint agent** that observes filesystem activity in real time, classifies behavioral intent, and performs automated containment and recovery using versioned snapshots.

The system is **behavior-driven**, not signature-based.

---

## Tech Stack
**Python**

 The system is implemented in Python to prioritize rapid iteration and clarity while exploring complex behavioral detection logic.
Language choice was driven by problem complexity and time constraints, not performance tuning at this stage.

---

## High-Level Flow

1. System startup
2. Concurrent worker threads initialized
3. Real-time filesystem observation
4. Stability-aware snapshot scheduling
5. Time-windowed behavioral intent classification
6. Escalation to containment on critical state
7. Automated restore

---

## Core Architecture

Pegasus operates as a **multi-threaded daemon**, with explicitly separated responsibilities.

---

## Worker Threads (I/O & Persistence)

### File Thread

Handles filesystem operations requested by the scheduler:

* snapshot creation
* file reads
* snapshot writes
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

* Monitors a **single user-configuredroot directory** (scope choice for v1)
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

## Restore Behavior

### Restore Backup Thread

On `CRITICAL`, Pegasus initiates automated recovery:

* restores from available snapshot history
* restored data is **bit-correct relative to the snapshot**
* restored content may be semantically stale but internally consistent

---

## Known Limitations

### User-Space Enforcement

* Process attribution and termination are best-effort
* Short-lived or forked processes may evade containment
* Kernel-level enforcement is out of scope
* Requires manual termination of the test_script process

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

### De-escaltion Semantics
* De-escalation logic is racy and unreliable.
* System may wait too long to cool down or remain in hot state post attacks.

---

### Optimization Pitholes
* Occasional O(N) time complexity dependence at places (intended for small number of files).
* System may break or become slow under real world stress.

---

## Feedback
Constructive technical critique and discussion are welcome via GitHub Issues.
Selected insights are summarized here over time.

---

## Scope & Non-Goals

Pegasus is not:

* a kernel-level EDR
* a signature-based scanner
* a guaranteed process killer
* a production-hardened security software

Pegasus is:

* a behavioral detection prototype
* a recovery-aware defensive agent
* a systems-engineering exploration

---

## Project Status

* Prototype (v1)
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

Create a `.env` file using `.env.example` as a template.

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

Terminate the process manually by pressing `Ctrl+C` from the keyboard.

Note:

* Some background workers block briefly during shutdown
* Forced termination interrupts cleanup tasks
* Multiple `Ctrl+C` prompts may be required to stop the agent

This behavior is expected for the current prototype version.

---

### Running Simulation (Test Script for Ransomware Behavior)

Open a second terminal window and execute:

```bash
python -m simulation.test_script
```
The Ransomware Test Script runs as a long running thread intended to mirror typical ransomware behavior and test the correctness of the prototype.

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
The Simulation runs as a long running thread and produces high-frequency file modifications, renames, and entropy shifts designed to trigger behavioral escalation and recovery flows. This script is intended to mirror typical ransomware behavior and test the correctness of the prototype.

This script is intended **only for local testing and demonstration**.

---

## Future Work

* Cleaner state de-escalation logic 
* Better optimization of system workflow
* Snapshot quarantine and retroactive invalidation
* Cleaner shutdown coordination
* Reduced shared-state coupling
* Optional kernel-level extensions (out of scope for v1)

---

## License

MIT

---

## Author

Soham Dawn

---

### Closing

Pegasus prioritizes **behavior, time, and recovery**—the most fundamental aspects of defensive systems.

Its limitations are explicit, bounded, and understood.

---
