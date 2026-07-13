#!/bin/sh
set -e

echo "SalesOS Backend starting..."
echo "Environment: ${SALESOS_ENV:-development}"
echo "Python: $(python --version)"

# Run migrations if requested
if [ "${RUN_MIGRATIONS}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

# Execute the main command
exec "$@"
