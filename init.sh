#!/usr/bin/env bash
# init.sh — Verificación mínima del entorno
#
# Solo valida que las herramientas base estén instaladas y que su versión
# sea compatible con este proyecto.

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()   { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

EXIT_CODE=0

echo "── 1. Verificando herramientas base ───────────────────"

check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 no está instalado"
    EXIT_CODE=1
    return
  fi

  local version
  version=$(python3 --version 2>&1)
  if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    ok "python3 -> ${version} (compatible, requiere >= 3.11)"
  else
    fail "python3 -> ${version} (incompatible, requiere >= 3.11)"
    EXIT_CODE=1
  fi
}

check_node() {
  if ! command -v node >/dev/null 2>&1; then
    fail "node no está instalado"
    EXIT_CODE=1
    return
  fi

  local version
  version=$(node --version 2>&1)
  if node -e 'const major = Number(process.versions.node.split(".")[0]); process.exit(major >= 18 ? 0 : 1)'; then
    ok "node -> ${version} (compatible, requiere >= 18)"
  else
    fail "node -> ${version} (incompatible, requiere >= 18)"
    EXIT_CODE=1
  fi
}

check_pnpm() {
  if ! command -v pnpm >/dev/null 2>&1; then
    fail "pnpm no está instalado"
    EXIT_CODE=1
    return
  fi

  local version
  version=$(pnpm --version 2>&1)
  if pnpm --version | awk -F. '{ exit ($1 >= 9 ? 0 : 1) }'; then
    ok "pnpm -> ${version} (compatible, requiere >= 9)"
  else
    fail "pnpm -> ${version} (incompatible, requiere >= 9)"
    EXIT_CODE=1
  fi
}

check_python
check_node
check_pnpm

echo ""
echo "── 2. Resumen ──────────────────────────────────────────"

if [ "$EXIT_CODE" -eq 0 ]; then
  ok "Entorno compatible para arrancar el proyecto."
else
  fail "Entorno no compatible. Instala/actualiza las herramientas marcadas."
fi

exit "$EXIT_CODE"
