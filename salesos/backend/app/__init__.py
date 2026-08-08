"""SalesOS backend application package.

Keep this module intentionally light. Eager imports of ``main`` / ``database``
here previously forced every ``import app.*`` (including Alembic env and
``check_alembic_head``) to load the full FastAPI stack — observed as Docker
``alembic current`` / config-import hangs on local compose (Wave 11 / Stream E).

Import concrete modules instead, e.g. ``from app.main import app``,
``from app.config import settings``.
"""
