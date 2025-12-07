#!/bin/sh
# Salir inmediatamente si un comando falla.
set -e

# Definir rutas
VENV_BIN_PATH="$HOME/.socialBots/bin"
PYTHON_SCRIPT="$HOME/usr/src/Python/deGitHub/botElectrico/botElectrico.py"
POST_SCRIPT="$HOME/usr/bin/postBotElectrico.sh"

# Definir rutas de log y error con marcas de tiempo para preservar el historial
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/botElectrico_${TIMESTAMP}.log"
ERR_FILE="/tmp/botElectrico_error_${TIMESTAMP}.log" # Nombre más claro para el archivo de errores

echo "Iniciando botElectrico.sh a las $TIMESTAMP..." | tee -a "$LOG_FILE"

# Activar el entorno virtual
# Se asume que el entorno virtual y sus dependencias (incluido kaleido)
# ya están configurados. La línea 'pip install' se ha eliminado de aquí.
. "$VENV_BIN_PATH/activate"

# Ejecutar el script principal de Python
echo "Ejecutando botElectrico.py..." | tee -a "$LOG_FILE"
"$VENV_BIN_PATH/python" "$PYTHON_SCRIPT" 2>>"$ERR_FILE" | tee -a "$LOG_FILE"

# Ejecutar el script de post-procesamiento
echo "Ejecutando postBotElectrico.sh..." | tee -a "$LOG_FILE"
"$POST_SCRIPT" 2>>"$ERR_FILE" | tee -a "$LOG_FILE"

# Desactivar el entorno virtual
deactivate

# Verificar si hubo errores y reportar
if [ -s "$ERR_FILE" ]; then
  echo "Error en botElectrico.sh. Verifique el archivo de error: $ERR_FILE" | tee -a "$LOG_FILE"
  cat "$ERR_FILE" | tee -a "$LOG_FILE" # También registrar los errores en el log principal
else
  echo "botElectrico.sh finalizado sin errores." | tee -a "$LOG_FILE"
fi

echo "Log completo en $LOG_FILE"
echo "Errores (si los hay) en $ERR_FILE"