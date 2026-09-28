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

-- Bootstrap may run against a partial database (e.g. salesos_test) before
-- every product schema has been created. Skip absent schemas rather than
-- aborting before the grants/default privileges for schemas that do exist.
DO $$
DECLARE
   schema_name text;
BEGIN
   FOREACH schema_name IN ARRAY ARRAY['public', 'audit', 'identity', 'company', 'activity', 'crm']
   LOOP
      IF to_regnamespace(schema_name) IS NOT NULL THEN
         EXECUTE format('GRANT USAGE ON SCHEMA %I TO salesos_app', schema_name);
         EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO salesos_app',
            schema_name
         );
         EXECUTE format(
            'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO salesos_app',
            schema_name
         );

         IF schema_name = 'public' THEN
            -- Source evidence is append-only. The runtime may mark a file
            -- complete and resolution may attach a row to a canonical UUID,
            -- but neither path may rewrite raw payloads or delete evidence.
            IF to_regclass('public.md_source_files') IS NOT NULL THEN
               REVOKE UPDATE, DELETE ON TABLE public.md_source_files FROM salesos_app;
               GRANT UPDATE (status) ON TABLE public.md_source_files TO salesos_app;
            END IF;
            IF to_regclass('public.md_source_rows') IS NOT NULL THEN
               REVOKE UPDATE, DELETE ON TABLE public.md_source_rows FROM salesos_app;
               GRANT UPDATE (global_entity_id) ON TABLE public.md_source_rows TO salesos_app;
            END IF;
            IF to_regclass('public.md_source_values') IS NOT NULL THEN
               REVOKE UPDATE, DELETE ON TABLE public.md_source_values FROM salesos_app;
            END IF;

            -- Spend ceilings are owned by SECURITY DEFINER functions
            -- (reserve_provider_spend, mark_provider_spend_in_flight,
            -- mark_provider_spend_unknown, release_provider_spend), all owned
            -- by the `salesos` owner role, so the accounting is enforced in the
            -- database rather than by the caller. Leaving UPDATE/DELETE on the
            -- table for salesos_app would hand the runtime a direct path to
            -- raise a limit or delete a reservation, skipping that accounting
            -- entirely. Read access is kept: the app needs to see the ceilings.
            IF to_regclass('public.provider_spend_limits') IS NOT NULL THEN
               REVOKE UPDATE, DELETE ON TABLE public.provider_spend_limits FROM salesos_app;
            END IF;

            -- Same reasoning for the reservation ledger: rows are created and
            -- transitioned by reserve_provider_spend / mark_provider_spend_in_flight
            -- / mark_provider_spend_unknown / release_provider_spend, all
            -- SECURITY DEFINER and owner-owned. A direct INSERT from the runtime
            -- would mint a reservation that never passed the atomic
            -- check-and-increment path, so the budget could be spent without
            -- being reserved. Read access stays for reporting.
            IF to_regclass('public.provider_spend_reservations') IS NOT NULL THEN
               REVOKE INSERT, UPDATE, DELETE
                  ON TABLE public.provider_spend_reservations FROM salesos_app;
            END IF;
         END IF;

         -- Future objects created by the owner role receive the same runtime
         -- privileges without a separate post-migration grant step.
         EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO salesos_app',
            schema_name
         );
         EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT USAGE, SELECT ON SEQUENCES TO salesos_app',
            schema_name
         );
      END IF;
   END LOOP;
END
$$;
