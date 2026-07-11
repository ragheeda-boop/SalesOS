#!/usr/bin/env bash
# SalesOS Dependency Updater
# Updates npm packages and Python packages to latest compatible versions.
# Usage: bash scripts/update-deps.sh [--dry-run]

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
DRY_RUN="${1:-}"

info()  { printf "\033[1;34m==>\033[0m %s\n" "$1"; }
ok()    { printf "\033[1;32m  ✓\033[0m %s\n" "$1"; }
warn()  { printf "\033[1;33m  ⚠\033[0m %s\n" "$1"; }
run()   {
    if [ "$DRY_RUN" = "--dry-run" ]; then
        warn "[DRY-RUN] Would execute: $*"
    else
        eval "$@"
    fi
}

# ── Frontend ──
info "Frontend (npm/pnpm)"
if [ -f "$ROOT_DIR/frontend/package.json" ]; then
    cd "$ROOT_DIR/frontend"
    if command -v pnpm &> /dev/null; then
        info "Using pnpm"
        run "pnpm update --latest"
        run "pnpm audit --fix"
        ok "pnpm dependencies updated"
    elif command -v npm &> /dev/null; then
        info "Using npm"
        run "npx npm-check-updates -u --packageFile package.json"
        run "npm install"
        run "npm audit fix --audit-level=high"
        ok "npm dependencies updated"
    fi
    cd "$ROOT_DIR"
fi

# ── Backend ──
info "Backend (Poetry)"
if [ -f "$ROOT_DIR/backend/pyproject.toml" ]; then
    cd "$ROOT_DIR/backend"
    if command -v poetry &> /dev/null; then
        run "poetry update"
        run "poetry check --lock"
        ok "Poetry dependencies updated"
    elif command -v pip &> /dev/null; then
        info "Using pip-compile"
        if [ -f requirements.in ]; then
            run "pip-compile --upgrade requirements.in"
        fi
        if [ -f dev-requirements.in ]; then
            run "pip-compile --upgrade dev-requirements.in"
        fi
        ok "pip dependencies updated"
    fi
    cd "$ROOT_DIR"
fi

# ── Generate SBOM ──
info "Generating SBOM"
run "pwsh -File '$ROOT_DIR/scripts/sbom.ps1'"
ok "SBOM generated"

# ── Summary ──
info "Summary"
if [ "$DRY_RUN" = "--dry-run" ]; then
    warn "Dry run completed — no changes made"
else
    ok "All dependencies updated"
fi
echo ""
echo "  Next steps:"
echo "    1. Run tests:    cd frontend && npm test"
echo "    2. Run lint:     cd frontend && npm run lint"
echo "    3. Typecheck:    cd frontend && npm run typecheck"
echo "    4. Backend:      cd backend && poetry run pytest"
echo "    5. Lint:         cd backend && poetry run ruff check ."
echo "    6. Typecheck:    cd backend && poetry run mypy ."
