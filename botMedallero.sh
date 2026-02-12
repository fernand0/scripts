#!/bin/sh
# Salir inmediatamente si un comando falla.
set -e

# Definir rutas
VENV_DIR="$HOME/.socialBots"
PYTHON_SCRIPT="$HOME/usr/src/Python/deGitHub/botMedallero/botMedallero.py"

# Definir rutas de log y error con marcas de tiempo
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/botMedallero_${TIMESTAMP}.log"
ERR_FILE="/tmp/botMedallero_error_${TIMESTAMP}.log"

echo "Iniciando botMedallero.sh a las $TIMESTAMP..." | tee -a "$LOG_FILE"

# Verificar si el entorno virtual existe y activarlo
if [ ! -d "$VENV_DIR" ]; then
  echo "Error: El entorno virtual '$VENV_DIR' no existe. Por favor, asegúrese de que esté configurado." | tee -a "$LOG_FILE"
  exit 1
fi

source "$VENV_DIR/bin/activate" || { echo "Error: No se pudo activar el entorno virtual '$VENV_DIR'."; exit 1; }

# Opcional: Asegurarse de que las dependencias estén instaladas
# Necesitaríamos saber las dependencias de botMedallero.py.
# Si las conoces, podemos añadirlas aquí.
# DEPS="dependencia1 dependencia2"
# echo "Verificando/actualizando dependencias..." | tee -a "$LOG_FILE"
# eval uv pip install $DEPS

# Ejecutar el script de Python
echo "Ejecutando botMedallero.py..." | tee -a "$LOG_FILE"
"$VENV_DIR/bin/python" "$PYTHON_SCRIPT" 2>>"$ERR_FILE" | tee -a "$LOG_FILE"

# Desactivar el entorno virtual
deactivate

# Verificar si hubo errores y reportar
if [ -s "$ERR_FILE" ]; then
  echo "Error en botMedallero.sh. Verifique el archivo de error: $ERR_FILE" | tee -a "$LOG_FILE"
  cat "$ERR_FILE" | tee -a "$LOG_FILE" # También registrar los errores en el log principal
else
  echo "botMedallero.sh finalizado sin errores." | tee -a "$LOG_FILE"
fi

echo "Log completo en $LOG_FILE"
echo "Errores (si los hay) en $ERR_FILE"