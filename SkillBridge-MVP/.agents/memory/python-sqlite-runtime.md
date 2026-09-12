---
name: Python SQLite runtime
description: Environment and SQLite transaction constraints relevant to the preserved SkillBridge backend.
---

The SkillBridge backend runs with the managed Python 3.11 module, and its SQLite connections use autocommit while retaining explicit commit calls in helpers.

**Why:** The base Python environment did not include pip-managed FastAPI dependencies, and Python 3.11 can retain a SQLite write lock after a failed foreign-key statement when a caller closes the connection without an explicit rollback; this broke the preserved Stage 2 suite.

**How to apply:** Keep Python dependencies in the root requirements file and install them through the workspace package workflow. Preserve the SQLite connection configuration unless transaction semantics are intentionally redesigned.