-- STORY-02-01 / R-14 remediation (docs/program/RISK_REGISTER.md, docs/program/DECISION_LOG.md DEC-013).
--
-- `salesos` (the role every other script/compose file in this repo
-- provisions) is a Postgres superuser with BYPASSRLS by virtue of being the
-- official pgvector/pgvector image's POSTGRES_USER bootstrap role.
-- Superusers and BYPASSRLS roles unconditionally bypass every RLS policy,
-- regardless of FORCE ROW LEVEL SECURITY — independently reproduced three
-- times (empty-WHERE-clause SELECT against a FORCE-enabled, correctly
-- policied table still returned both tenants' rows). This role is additive:
-- `salesos` is kept, unchanged, as the migration/owner role — application
-- runtime traffic connects as this role instead.
--
-- Runs automatically on first container init (mounted alongside 01-init.sql).
-- For an already-initialized data volume (the common case — Postgres only
-- executes /docker-entrypoint-initdb.d/ scripts once, against an empty data
-- directory), apply manually:
--   docker exec -i salesos-postgres-1 psql -U salesos -d salesos < infra/docker/postgres/init/02-app-role.sql
--   docker exec -i salesos-postgres-1 psql -U salesos -d salesos_test < infra/docker/postgres/init/02-app-role.sql

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'salesos_app') THEN
      CREATE ROLE salesos_app
        NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION
        LOGIN PASSWORD 'salesos_app_dev_password';
   END IF;
END
$$;

-- Dynamic, not a literal "salesos": this script also runs against
-- salesos_test (local/CI) and any other POSTGRES_DB name a given environment
-- uses. A hardcoded `GRANT CONNECT ON DATABASE salesos` only ever worked by
-- coincidence on hosts where a database literally named `salesos` happened
-- to also exist on the same server — it fails outright (`database "salesos"
-- does not exist`) on a single-database instance named anything else, as
-- found while wiring this into CI's ephemeral salesos_test service container.
DO $$
BEGIN
   EXECUTE format('GRANT CONNECT ON DATABASE %I TO salesos_app', current_database());
END
$$;

GRANT USAGE ON SCHEMA public, audit, identity, company, activity, crm TO salesos_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public, audit, identity, company, activity, crm TO salesos_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public, audit, identity, company, activity, crm TO salesos_app;

-- Tables/sequences that don't exist yet (future Alembic migrations, run as
-- the owning `salesos` role) are covered automatically — without this,
-- every new migration would silently need a follow-up GRANT or the app
-- would start getting permission-denied errors on brand-new tables.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT USAGE, SELECT ON SEQUENCES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA company GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA company GRANT USAGE, SELECT ON SEQUENCES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA activity GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA activity GRANT USAGE, SELECT ON SEQUENCES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA crm GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA crm GRANT USAGE, SELECT ON SEQUENCES TO salesos_app;
