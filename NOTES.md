## Session — Phase 4 complete (2026-08-09)

**Built:**
- FastAPI REST API (src/api.py): POST /dags (submit, validates task
  types against TASK_REGISTRY), GET /tasks, GET /tasks/{id},
  POST /tasks/{id}/cancel
- WebSocket endpoint (/ws/status) pushing full task list every 2s
- Static dashboard (static/index.html) — summary cards + live table,
  color-coded by status, cancel buttons on pending/queued tasks

**Verified:**
- Submitted a 2-task DAG via API, confirmed correct execution order
  and Postgres state (extract -> success, clean -> success, correct
  dependency array)
- Cancel endpoint confirmed clean — cancelled 'notify' before pickup,
  confirmed start_time/end_time stayed NULL, no worker touched it
- Live dashboard confirmed showing simultaneous mixed states
  (pending/queued/running/success) across tasks in one WebSocket push,
  and watched a single task transition pending -> queued -> running ->
  success live without page refresh

**Known limitations (documented, not blocking):**
- Cancel has a race condition: if a task is already 'queued' when
  cancelled, a worker that already grabbed the message may still
  execute it, since execute_task() doesn't re-check status before
  running. Acceptable for this project's scope; a production version
  would have the worker verify status != 'cancelled' before executing.
- Design choice: DAG submission only accepts task IDs already
  registered in TASK_REGISTRY (can't submit arbitrary code) --
  intentional security boundary, same pattern Airflow uses with
  pre-registered operators.

## Interview Stories

### Story 1: Heartbeat and Lease Crash Recovery
During testing, we needed to prove the system's resilience to worker crashes. I manually forced a worker to crash mid-task by identifying its true PID and sending a kill signal. I then watched the scheduler detect the stale heartbeat and reassign the task to a different queue, where a second worker successfully picked it up and completed it. This was a great exercise in understanding the heartbeat/lease pattern and the tradeoffs of polling-based staleness detection, as well as the practical challenges of debugging phantom processes in the terminal.

### Story 2: The Scheduler Indentation Bug
We encountered a subtle bug where an editor's auto-formatter silently changed the indentation of a `mark_queued()` call, pushing it outside of its active database connection's `with` block. Since the linter suppressed the warning, the issue was masked. I ultimately discovered it by using the command line to read the raw source code instead of trusting the editor's visual representation. This reinforced the importance of verifying code from the source of truth rather than blindly trusting developer tooling.

### Story 3: Idempotency Under Real Crash Conditions
I designed a test to ensure side effects are idempotent when a crash occurs after a database commit but before the task is marked complete. By forcing a crash in this exact window, the task was retried. Using an `idempotency_log` and a counter table, I verified that the retried execution correctly skipped the already-applied side effect while still transitioning to a success state. This test validates our design against a critical production hazard—duplicate side effects on retry—proving the system's robustness rather than just assuming it works.
