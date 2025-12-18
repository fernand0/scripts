#!/bin/bash
# set -x
# Salir inmediatamente si un comando falla.
set -e

# --- Argumentos por defecto ---
VENV_DIR="$HOME/.socialBots"
DEPS=""
POST_SCRIPT=""
PRE_SCRIPT=""
SCRIPT_NAME=""
PYTHON_SCRIPT=""
PYTHON_ARGS=""

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
  echo "  -d, --deps "DEP1..."  Lista de dependencias de Python a instalar."
  echo "  -p, --post-script RUTA  Script a ejecutar después del script de Python."
  echo "  -e, --pre-script RUTA   Script a ejecutar antes del script de Python."
  echo "  -a, --args "ARG1..."  Argumentos para el script de Python."
  echo "  -h, --help            Muestra esta ayuda."
  exit 1
}

# --- Parseo de argumentos ---
while [ "$#" -gt 0 ]; do
  case "$1" in
    -v|--venv) VENV_DIR="$2"; shift 2;;
    -d|--deps) DEPS="$2"; shift 2;;
    -p|--post-script) POST_SCRIPT="$2"; shift 2;;
    -e|--pre-script) PRE_SCRIPT="$2"; shift 2;;
    -a|--args) PYTHON_ARGS="$2"; shift 2;;
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

# --- Configuración de logs y TRAP ---
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/${SCRIPT_NAME}_${TIMESTAMP}.log"
ERR_FILE="/tmp/${SCRIPT_NAME}_error_${TIMESTAMP}.log"

cleanup() {
  # Desactivar entorno virtual si está activo
  if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
  fi
  
  # Verificar si hubo errores y reportar
  if [ -s "$ERR_FILE" ]; then
    echo "ERROR en $SCRIPT_NAME. Ver log de errores: $ERR_FILE" >&2
    cat "$ERR_FILE" >&2
  else
    echo "$SCRIPT_NAME finalizado sin errores." | tee -a "$LOG_FILE"
  fi
  echo "Log completo en: $LOG_FILE" | tee -a "$LOG_FILE"
}
trap cleanup EXIT

# --- INICIO DEL SCRIPT ---
echo "Iniciando $SCRIPT_NAME a las $TIMESTAMP..." | tee -a "$LOG_FILE"

# Activar entorno virtual
if [ ! -d "$VENV_DIR" ]; then
  echo "Error: El directorio del entorno virtual '$VENV_DIR' no existe." | tee -a "$LOG_FILE"
  exit 1
fi
source "$VENV_DIR/bin/activate" || { echo "Error al activar el entorno virtual."; exit 1; }

# Instalar dependencias si se especificaron
if [ -n "$DEPS" ]; then
  echo "Instalando/actualizando dependencias: $DEPS" | tee -a "$LOG_FILE"
  if [[ "$DEPS" == *"git+"* ]]; then
    uv pip install "$DEPS" >>"$LOG_FILE" 2>&1
  else
    uv pip install $DEPS >>"$LOG_FILE" 2>&1
  fi
fi

# Ejecutar pre-script si se especificó
if [ -n "$PRE_SCRIPT" ]; then
  echo "Ejecutando pre-script: $PRE_SCRIPT" | tee -a "$LOG_FILE"
  "$PRE_SCRIPT" 2> >(tee -a "$ERR_FILE" >&2) | tee -a "$LOG_FILE"
fi

# Ejecutar script principal de Python
echo "Ejecutando script de Python: $PYTHON_SCRIPT $PYTHON_ARGS" | tee -a "$LOG_FILE"
"$VENV_DIR/bin/python" "$PYTHON_SCRIPT" $PYTHON_ARGS 2> >(tee -a "$ERR_FILE" >&2) | tee -a "$LOG_FILE"

# Ejecutar post-script si se especificó
if [ -n "$POST_SCRIPT" ]; then
  echo "Ejecutando post-script: $POST_SCRIPT" | tee -a "$LOG_FILE"
  "$POST_SCRIPT" 2> >(tee -a "$ERR_FILE" >&2) | tee -a "$LOG_FILE"
fi
