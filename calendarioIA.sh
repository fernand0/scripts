#!/usr/bin/env bash
set -eo pipefail

# Directory where manage-agenda project is located
AGENDA_DIR="${AGENDA_DIR:-$HOME/usr/src/Python/deGitHub/manage-agenda}"

# Log configuration
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${LOG_DIR:-/tmp}"
LOG_FILE="${LOG_DIR}/agenda_${TIMESTAMP}.log"
LATEST_LOG="${LOG_DIR}/agenda.txt"

# Flags & defaults
VERBOSE="-v"
RUN_MOVE=true

usage() {
    cat <<EOF
Uso: $(basename "$0") [OPCIONES] [PASOS...]

Ejecuta las tareas periódicas de manage-agenda (IMAP, Gmail, Web y Move).

Pasos disponibles:
  imap        Procesa mensajes por IMAP (add -s imap)
  gmail       Procesa correos de Gmail (add -s gmail)
  web         Procesa fuentes web (add -s web)
  move        Mueve eventos entre calendarios (move -i)

Opciones:
  --no-move   Omite el paso interactivo de 'move'
  -q, --quiet Ejecuta sin salida detallada (sin -v)
  -h, --help  Muestra esta ayuda

Si no se especifican pasos, se ejecutan todos en secuencia.
EOF
    exit 0
}

# Parse options
STEPS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-move)
            RUN_MOVE=false
            shift
            ;;
        -q|--quiet)
            VERBOSE=""
            shift
            ;;
        -h|--help)
            usage
            ;;
        imap|gmail|web|move)
            STEPS+=("$1")
            shift
            ;;
        *)
            echo "Error: Opción o paso desconocido: $1" >&2
            usage
            ;;
    esac
done

# If no specific steps were passed, run the standard pipeline
if [[ ${#STEPS[@]} -eq 0 ]]; then
    STEPS=("imap" "gmail" "web")
    if [[ "$RUN_MOVE" == true ]]; then
        STEPS+=("move")
    fi
fi

# Ensure manage-agenda repo exists
if [[ ! -d "$AGENDA_DIR" ]]; then
    echo "Error: No se encontró el proyecto manage-agenda en '$AGENDA_DIR'" >&2
    exit 1
fi

log() {
    local msg="[$(date +'%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

# Initialize log file and link latest
: > "$LOG_FILE"
ln -sf "$LOG_FILE" "$LATEST_LOG"

log "=== Iniciando sincronización de agenda ==="

run_manage_agenda() {
    uv --directory "$AGENDA_DIR" run manage-agenda "$@" 2>&1 | tee -a "$LOG_FILE"
}

for step in "${STEPS[@]}"; do
    case "$step" in
        imap)
            log "--- Paso: Añadir eventos desde IMAP ---"
            run_manage_agenda $VERBOSE add -s imap || log "Advertencia: Falló el paso IMAP"
            ;;
        gmail)
            log "--- Paso: Añadir eventos desde Gmail ---"
            run_manage_agenda $VERBOSE add -s gmail || log "Advertencia: Falló el paso Gmail"
            ;;
        web)
            log "--- Paso: Añadir eventos desde Web ---"
            run_manage_agenda $VERBOSE add -s web || log "Advertencia: Falló el paso Web"
            ;;
        move)
            # Only run interactive move if standard input is a terminal or explicitly requested
            if [[ -t 0 ]]; then
                log "--- Paso: Mover eventos (interactivo) ---"
                run_manage_agenda $VERBOSE move -i || log "Advertencia: Falló el paso Move"
            else
                log "--- Paso: Omitiendo 'move -i' (no hay terminal interactiva) ---"
            fi
            ;;
    esac
done

log "=== Sincronización completada. Log guardado en $LOG_FILE (enlazado a $LATEST_LOG) ==="
