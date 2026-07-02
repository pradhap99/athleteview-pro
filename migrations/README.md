# migrations/

**Guardrail: do not hand-write or auto-generate migrations here without human approval**
(see root `CLAUDE.md`). Schema changes to the single source of truth (PostgreSQL) are a
reviewed, deliberate step.

- **Dev / unit tests** create tables from the SQLAlchemy metadata via
  `throughline_api.db.init_db` — no migration needed.
- **Production** will use Alembic migrations added here intentionally, one reviewed PR at a
  time, once the schema stabilizes. The event log (`events`) is append-only; projection
  tables are rebuildable, so most projection changes are code-only (replay), not DDL.
