#!/usr/bin/env bash
# Reglas automáticas del Parcial · Corte 1 (semanas 1 a 4).
#
# Uso:
#   scripts/verificar_estructura.sh              # informa; solo falla por incumplimientos en lo ya iniciado
#   scripts/verificar_estructura.sh --estricto   # además falla por lo que aún está pendiente (úselo antes de entregar)
#
# Código de salida: 0 = sin errores, 1 = hay errores.
set -u

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ" || exit 2

ESTRICTO=0
[ "${1:-}" = "--estricto" ] && ESTRICTO=1

SERVICIOS="ms-catalogo ms-inventario ms-pagos ms-pedidos bff-web ms-confiabilidad"
errores=0
pendientes=0

ok()   { echo "  [OK]    $*"; }
mal()  { echo "  [ERROR] $*"; errores=$((errores + 1)); }
pend() { echo "  [PEND]  $*"; pendientes=$((pendientes + 1)); }

echo "== Reglas globales =="

# 1. Sin secretos ni entornos virtuales versionados.
versionados="$(git ls-files 2>/dev/null | grep -E '(^|/)\.env$|(^|/)\.venv/' || true)"
if [ -n "$versionados" ]; then
  mal "Archivos que no deben versionarse (.env o .venv):"; echo "$versionados" | sed 's/^/           /'
else
  ok "No hay .env ni .venv versionados"
fi

# 2. .gitignore protege .env y .venv.
if [ -f .gitignore ] && grep -qE '^\.env$' .gitignore && grep -qE '^\.venv/?$' .gitignore; then
  ok ".gitignore incluye .env y .venv"
else
  mal ".gitignore debe incluir las líneas '.env' y '.venv/'"
fi

# 3. Patrones obvios de credenciales en archivos versionados (heurística, no sustituye la revisión).
sospechosos="$(git grep -I -i -n -E '(password|passwd|secret|token|api[_-]?key)[[:space:]]*[:=][[:space:]]*["'\'']?[A-Za-z0-9/+_-]{8,}' -- \
  ':!docs' ':!paquetes' ':!README.md' ':!scripts/verificar_estructura.sh' ':!ruleta' ':!*.example' 2>/dev/null || true)"
if [ -n "$sospechosos" ]; then
  mal "Posibles credenciales escritas en el código (revise y rote si son reales):"; echo "$sospechosos" | head -10 | sed 's/^/           /'
else
  ok "No se detectan credenciales evidentes"
fi

echo
echo "== Servicios (carpeta servicios/) =="
for s in $SERVICIOS; do
  d="servicios/$s"
  echo "- $s"
  if [ ! -f "$d/pyproject.toml" ]; then
    pend "Aún no iniciado (falta $d/pyproject.toml)"
    continue
  fi
  for f in uv.lock Dockerfile README.md app/main.py app/config.py; do
    [ -f "$d/$f" ] && ok "$f" || mal "Falta $d/$f"
  done
  if ls "$d"/tests/test_*.py >/dev/null 2>&1; then ok "tests/ con pruebas"; else mal "Faltan pruebas en $d/tests/test_*.py"; fi

  # Regla de arquitectura: la capa de servicio no puede conocer FastAPI.
  if [ -d "$d/app/servicios" ]; then
    uso="$(grep -rIn --include='*.py' -iE '^[[:space:]]*(from|import)[[:space:]]+(fastapi|starlette)' "$d/app/servicios" || true)"
    if [ -n "$uso" ]; then mal "La capa de servicio importa FastAPI/Starlette:"; echo "$uso" | sed 's/^/           /'; else ok "app/servicios sin FastAPI"; fi
  else
    mal "Falta la capa $d/app/servicios"
  fi

  # Prohibido usar requests.
  req="$(grep -rIn --include='*.py' -E '^[[:space:]]*(import requests|from requests)' "$d/app" 2>/dev/null || true)"
  if [ -n "$req" ]; then mal "Se usa la biblioteca requests (prohibida):"; echo "$req" | sed 's/^/           /'; else ok "Sin requests"; fi
done

echo
echo "== Plataforma, configuración y documentación =="
req_dir() {  # $1 = ruta, $2 = etiqueta
  if [ -d "$1" ] && [ -n "$(find "$1" -type f ! -name '.gitkeep' ! -name 'LEEME-PENDIENTE.md' 2>/dev/null | head -1)" ]; then ok "$2"; else pend "$2 (sin contenido aún en $1)"; fi
}
req_dir plataforma/consul        "A08 Consul (plataforma/consul)"
req_dir plataforma/descubrimiento "A08 Descubrimiento (plataforma/descubrimiento)"
req_dir plataforma/balanceador   "A09 Balanceador (plataforma/balanceador)"
req_dir config-repo              "A07 config-repo"
req_dir tests                    "A10 Pruebas (tests/)"
req_dir docs/arquitectura        "A11 Arquitectura (docs/arquitectura)"
[ -f docker-compose.yml ] && ok "A12 docker-compose.yml" || pend "A12 docker-compose.yml"
[ -f scripts/e2e.sh ]     && ok "A12 scripts/e2e.sh"     || pend "A12 scripts/e2e.sh"
[ -f docs/E2E.md ]        && ok "A12 docs/E2E.md"        || pend "A12 docs/E2E.md"

echo
echo "Resumen: $errores error(es), $pendientes pendiente(s)."
if [ "$errores" -gt 0 ]; then exit 1; fi
if [ "$ESTRICTO" -eq 1 ] && [ "$pendientes" -gt 0 ]; then
  echo "Modo estricto: hay elementos pendientes."; exit 1
fi
exit 0
