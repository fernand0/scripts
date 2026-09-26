#!/bin/sh
# Salir inmediatamente si un comando falla.
set -e

# Definir el entorno virtual para r2e
VENV_DIR="$HOME/.socialBots"
R2E_COMMAND="$VENV_DIR/bin/r2e" # Comando r2e dentro del venv

# Definir rutas de log y error con marcas de tiempo
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/r2e_${TIMESTAMP}.log"
ERR_FILE="/tmp/r2e_error_${TIMESTAMP}.log"

# Dependencias para r2e
DEPS="rss2email"

echo "Iniciando r2e.sh a las $TIMESTAMP..." > "$LOG_FILE"

# Crear el entorno virtual e instalar dependencias si no existe
if [ ! -d "$VENV_DIR" ]; then
  echo "El entorno virtual '$VENV_DIR' no existe. Creándolo..." > "$LOG_FILE"
  uv venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  echo "Instalando dependencias: $DEPS" > "$LOG_FILE"
  eval uv pip install $DEPS
  deactivate
  echo "Entorno creado y configurado." > "$LOG_FILE"
fi

# Activar el entorno y ejecutar r2e
echo "Activando entorno '$VENV_DIR' y ejecutando r2e..." > "$LOG_FILE"
source "$VENV_DIR/bin/activate" > "$LOG_FILE" || { echo "Error: No se pudo activar el entorno virtual '$VENV_DIR'."; exit 1; }

# Opcional: Asegurarse de que las dependencias estén instaladas (rápido si ya existen)
echo "Verificando/actualizando dependencias..." > "$LOG_FILE"
uv pip install $DEPS > "$LOG_FILE" 2>&1

# Ejecutar el comando r2e
echo "Ejecutando r2e run..." > "$LOG_FILE"
"$R2E_COMMAND" run 2>>"$ERR_FILE" > "$LOG_FILE"

# Desactivar el entorno virtual
deactivate

# Verificar si hubo errores y reportar
if [ -s "$ERR_FILE" ]; then
  echo "Error en r2e.sh. Verifique el archivo de error: $ERR_FILE" > "$LOG_FILE"
  cat "$ERR_FILE" > "$LOG_FILE" # También registrar los errores en el log principal
else
  echo "r2e.sh finalizado sin errores." > "$LOG_FILE"
fi

echo "Log completo en $LOG_FILE" > "$LOG_FILE"
echo "Errores (si los hay) en $ERR_FILE" > "$LOG_FILE"
