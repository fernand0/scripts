#!/bin/bash
# set -x
# Salir inmediatamente si un comando falla.
set -e -o pipefail

# --- Argumentos por defecto ---
VENV_DIR="$HOME/.socialBots"
DEPS=()
POST_SCRIPT=""
PRE_SCRIPT=""
SCRIPT_NAME=""
PYTHON_SCRIPT=""
PYTHON_ARGS=()

# --- Función de ayuda ---
usage() {
  echo "Uso: $0 [OPCIONES] <nombre_script> <script_python>"
  echo
  echo "Argumentos obligatorios:"
  echo "  nombre_script         Nombre corto para identificar el proceso (usado en logs)."
  echo "  script_python         Ruta al script de Python a ejecutar."
  echo
  echo "Opciones:"
  echo "  -v, --venv RUTA       Ruta al entorno virtual (por defecto: $HOME/.socialBots)."
  echo "  -d, --deps DEP       Dependencia de Python a instalar; se puede repetir."
  echo "  -p, --post-script RUTA  Script a ejecutar después del script de Python."
  echo "  -e, --pre-script RUTA   Script a ejecutar antes del script de Python."
  echo "  -a, --args ARG       Argumento para el script de Python; se puede repetir."
  echo "  -h, --help            Muestra esta ayuda."
  exit 1
}

# --- Parseo de argumentos ---
while [ "$#" -gt 0 ]; do
  case "$1" in
    -v|--venv) VENV_DIR="$2"; shift 2;;
    -d|--deps) DEPS+=("$2"); shift 2;;
    -p|--post-script) POST_SCRIPT="$2"; shift 2;;
    -e|--pre-script) PRE_SCRIPT="$2"; shift 2;;
    -a|--args) PYTHON_ARGS+=("$2"); shift 2;;
    -h|--help) usage;;
    -*) echo "Opción desconocida: $1"; usage;;
    *) 
      if [ -z "$SCRIPT_NAME" ]; then
        SCRIPT_NAME="$1"
      elif [ -z "$PYTHON_SCRIPT" ]; then
        PYTHON_SCRIPT="$1"
      else
        echo "Argumentos inesperados: $1"; usage;
      fi
      shift 1;;
  esac
done

# --- Validar argumentos obligatorios ---
if [ -z "$SCRIPT_NAME" ] || [ -z "$PYTHON_SCRIPT" ]; then
  echo "Error: Faltan argumentos obligatorios."
  usage
fi
export SCRIPT_NAME

# --- Configuración de logs y TRAP ---
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/${SCRIPT_NAME}_${TIMESTAMP}.log"
ERR_FILE="/tmp/${SCRIPT_NAME}_error_${TIMESTAMP}.log"

cleanup() {
  local exit_code=$?
  # Desactivar entorno virtual si está activo
  if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
  fi
  
  # Si hubo errores o código de salida distinto de 0, emitir a stderr para que cron envíe el correo
  if [ -s "$ERR_FILE" ] || [ "$exit_code" -ne 0 ]; then
    {
      echo "ERROR en $SCRIPT_NAME a las $TIMESTAMP (código de salida: $exit_code)"
      if [ -s "$ERR_FILE" ]; then
        echo "--- Detalle de errores ($ERR_FILE) ---"
        cat "$ERR_FILE"
      fi
      echo "Log completo disponible en: $LOG_FILE"
    } >&2
  else
    # Si no hubo errores, eliminamos el archivo de error vacío
    rm -f "$ERR_FILE"
  fi
  return 0
}
trap cleanup EXIT

# --- INICIO DEL SCRIPT ---
echo "Iniciando $SCRIPT_NAME a las $TIMESTAMP..." >> "$LOG_FILE"

# Activar entorno virtual
if [ ! -d "$VENV_DIR" ]; then
  echo "Error: El directorio del entorno virtual '$VENV_DIR' no existe." >> "$ERR_FILE"
  exit 1
fi
source "$VENV_DIR/bin/activate" 2>> "$ERR_FILE" || { echo "Error al activar el entorno virtual." >> "$ERR_FILE"; exit 1; }

# Instalar dependencias si se especificaron
if [ ${#DEPS[@]} -gt 0 ]; then
  echo "Instalando/actualizando dependencias: ${DEPS[*]}" >> "$LOG_FILE"
  uv pip install "${DEPS[@]}" >> "$LOG_FILE" 2>> "$ERR_FILE"
fi

# Ejecutar pre-script si se especificó
if [ -n "$PRE_SCRIPT" ]; then
  echo "Ejecutando pre-script: $PRE_SCRIPT" >> "$LOG_FILE"
  "$PRE_SCRIPT" >> "$LOG_FILE" 2>> "$ERR_FILE"
fi

# Ejecutar script principal de Python
echo "Ejecutando script de Python: $PYTHON_SCRIPT ${PYTHON_ARGS[*]}" >> "$LOG_FILE"
"$VENV_DIR/bin/python" "$PYTHON_SCRIPT" "${PYTHON_ARGS[@]}" >> "$LOG_FILE" 2>> "$ERR_FILE"

# Ejecutar post-script si se especificó
if [ -n "$POST_SCRIPT" ]; then
  echo "Ejecutando post-script: $POST_SCRIPT" >> "$LOG_FILE"
  "$POST_SCRIPT" >> "$LOG_FILE" 2>> "$ERR_FILE"
fi
