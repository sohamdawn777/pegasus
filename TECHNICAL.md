# Pegasus

## Behavioral File-System Telemetry, Containment & Recovery Agent (Prototype v1)

Pegasus is a user-space Linux endpoint agent that observes filesystem
activity in real time, classifies behavioral intent, and performs
automated containment and recovery using versioned snapshots.

The system is behavior-driven, not signature-based.

## Tech Stack

### Python

The system is implemented in Python to prioritize rapid iteration and
clarity while exploring complex behavioral detection logic. Language
choice was driven by problem complexity and time constraints, not
performance tuning at this stage.

## High-Level Flow

-   System startup
-   Concurrent worker threads initialized
-   Real-time filesystem observation
-   Stability-aware snapshot scheduling
-   Time-windowed behavioral intent classification
-   Escalation to containment on critical state
-   Automated restore

## Core Architecture

Pegasus operates as a multi-threaded daemon, with explicitly separated
responsibilities.

### Worker Threads (I/O & Persistence)

#### File Thread

Handles filesystem operations requested by the scheduler:

-   Snapshot creation
-   File reads
-   Snapshot writes
-   Cleanup actions

Operations are serialized through an internal task queue to avoid direct
contention.

#### Database Thread

Handles all persistence operations using SQLite:

-   Snapshot metadata
-   Version flags
-   Lifecycle state

Database access is isolated to this thread to maintain consistency.

## Filesystem Observation & Snapshot Scheduling

### Observer Thread

Monitors a single user-configured root directory (scope choice for v1).

Recursively observes all subdirectories and files.

Captures:

-   Create / modify / delete / rename events
-   Timestamps
-   Rename metadata

The observer populates shared in-memory structures:

-   A file dictionary (live file state)
-   A heap (scheduled snapshot candidates)

### Scheduler Thread

Consumes entries from the heap.

Applies a stability window to avoid mid-write snapshotting.

Validates heap entries against the file dictionary to discard stale
events.

Dispatches snapshot tasks to the file thread.

This pipeline approximates real-time snapshotting without relying on
filesystem journaling.

## Version Lifecycle Management

### Version Controller Thread

Periodically evaluates snapshot age and relevance.

Updates database flags indicating whether versions are safe to delete.

### File Auditor Thread

Reads version flags from the database.

Performs asynchronous physical deletion of obsolete snapshots.

This decouples logical versioning from physical cleanup.

## Behavioral Detection Pipeline

### Intent Classifier Thread

The intent classifier runs periodically using time-windowed analysis.

It consumes snapshots of the file dictionary and evaluates behavior
using multiple detectors, including:

-   Burst modification frequency
-   Inter-event timing deltas
-   Entropy delta (relative change)
-   ASCII ratio fallback for unknown formats
-   Rename and extension mutation detection
-   Directory-level multi-file correlation

Classification occurs across three layers:

1.  Per-file intent scoring
2.  Directory aggregation
3.  Global system state machine:
    -   `SAFE`
    -   `WARNING`
    -   `CRITICAL`

## Containment & Escalation

When `CRITICAL` is reached, the intent classifier signals containment.

### Process Monitor Thread

Attempts best-effort attribution and termination using process
heuristics.

Uses filesystem context and runtime metadata.

### Fallback Containment

If reliable termination is not possible, Pegasus enforces directory
locking to prevent further damage.

Containment prioritizes damage limitation, not perfect attribution.

## Snapshot Invariants & Recovery Semantics

Pegasus enforces strict snapshot rules based on system state:

### SAFE

Snapshots taken normally.

### WARNING

Snapshots taken but flagged as potentially compromised.

### CRITICAL

Snapshotting stops immediately.

## Restore Behavior

### Restore Backup Thread

On `CRITICAL`, Pegasus initiates automated recovery:

-   Restores from available snapshot history
-   Restored data is bit-correct relative to the snapshot
-   Restored content may be semantically stale but internally consistent

## Known Limitations

### User-Space Enforcement

-   Process attribution and termination are best-effort.
-   Short-lived or forked processes may evade containment.
-   Kernel-level enforcement is out of scope.
-   Requires manual termination of the `test_script` process.

### Temporal Classification Lag

Intent detection occurs after a time window.

Some snapshots may predate escalation.

Restored data may not represent the most recent semantic version.

### Shutdown Semantics

Some threads may block on waits.

Unified shutdown coordination is incomplete.

Forced termination may interrupt background tasks.

### Shared State Coupling

Central shared structures increase coupling.

Message-passing refactors are deferred to later versions.

### De-escalation Semantics

De-escalation logic is racy and unreliable.

The system may wait too long to cool down or remain in a hot state
post-attacks.

### Optimization Pitfalls

Occasional `O(N)` time complexity dependence exists at places (intended
for a small number of files).

The system may break or become slow under real-world stress.

## Feedback

Constructive technical critique and discussion are welcome via GitHub
Issues. Selected insights are summarized here over time.

## Scope & Non-Goals

Pegasus is not:

-   A kernel-level EDR
-   A signature-based scanner
-   A guaranteed process killer
-   Production-hardened security software

Pegasus is:

-   A behavioral detection prototype
-   A recovery-aware defensive agent
-   A systems-engineering exploration

## Project Status

**Prototype (v1)**

Suitable for freeze and evaluation.

## Installation

Pegasus is designed to run on Linux as a user-space daemon.

### Requirements

-   Linux (tested on modern distributions)
-   Python 3.10+
-   POSIX filesystem with inotify support
-   SQLite 3 (local file-based database)
-   Sufficient permissions to:
    -   Observe filesystem events
    -   Read/write monitored directories
    -   Attempt best-effort process inspection

### Setup

Create a `.env` file using `.env.example` as a template.

Clone the repository:

``` bash
git clone https://github.com/sohamdawn777/pegasus.git
cd pegasus
```

Create and activate a virtual environment:

``` bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

## Running Pegasus

Start the agent:

``` bash
python -m backend.main
```

Pegasus runs as a long-lived process and begins monitoring immediately
after startup.

Logs and state transitions are emitted continuously during runtime.

## Stopping the Agent

Terminate the process manually by pressing `Ctrl+C` from the keyboard.

### Note

-   Some background workers block briefly during shutdown.
-   Forced termination interrupts cleanup tasks.
-   Multiple `Ctrl+C` prompts may be required to stop the agent.
-   This behavior is expected for the current prototype version.

## Running Simulation (Test Script for Ransomware Behavior)

Open a second terminal window and execute:

``` bash
python -m simulation.test_script
```

The Ransomware Test Script runs as a long-running thread intended to
mirror typical ransomware behavior and test the correctness of the
prototype.

## Deployment Notes

Pegasus is intended to be run in controlled environments.

Running as a privileged user may improve visibility but is not required.

Kernel-level enforcement is outside the scope of this version.

It is strongly recommended to only use dummy data inside the folder to
be monitored by the system.

Use of real data may lead to unwanted data corruption or loss due to
abnormal system behavior.

## Simulating Attacks

To generate controlled destructive filesystem activity for testing,
activate the same virtual environment (`venv`) in a separate terminal
and run the simulation script while Pegasus is active:

``` bash
python -m simulation.test_script
```

The simulation runs as a long-running thread and produces high-frequency
file modifications, renames, and entropy shifts designed to trigger
behavioral escalation and recovery flows. This script is intended to
mirror typical ransomware behavior and test the correctness of the
prototype.

This script is intended only for local testing and demonstration.

## Future Work

-   Cleaner state de-escalation logic
-   Better optimization of system workflow
-   Snapshot quarantine and retroactive invalidation
-   Cleaner shutdown coordination
-   Reduced shared-state coupling
-   Optional kernel-level extensions (out of scope for v1)

## License

MIT

## Author

Soham Dawn

## Closing

Pegasus prioritizes behavior, time, and recovery---the most fundamental
aspects of defensive systems.

Its limitations are explicit, bounded, and understood.
