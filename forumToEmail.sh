#!/bin/sh
# Salir inmediatamente si un comando falla.
set -e

# Definir el entorno virtual a usar
VENV_DIR="$HOME/.socialBots" # Cambiado a .socialBots
PYTHON_SCRIPT="$HOME/usr/src/scripts/forumToEmail.py"

# Definir rutas de log y error con marcas de tiempo
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/forumToEmail_${TIMESTAMP}.log"
ERR_FILE="/tmp/forumToEmail_error_${TIMESTAMP}.log"

echo "Iniciando forumToEmail.sh a las $TIMESTAMP..." > "$LOG_FILE"

# Verificar si el entorno virtual existe y activarlo
if [ ! -d "$VENV_DIR" ]; then
  echo "Error: El entorno virtual '$VENV_DIR' no existe. Por favor, asegúrese de que esté configurado." > "$LOG_FILE"
  exit 1
fi

source "$VENV_DIR/bin/activate" || { echo "Error: No se pudo activar el entorno virtual '$VENV_DIR'."; exit 1; }

# Opcional: Asegurarse de que las dependencias estén instaladas
# Para esto, necesitaríamos saber las dependencias de forumToEmail.py.
# Si las conoces, podemos añadirlas aquí.
DEPS="jinja2"
echo "Verificando/actualizando dependencias..." > "$LOG_FILE"
uv pip install $DEPS > "$LOG_FILE" 2>&1

# Ejecutar el script de Python
echo "Ejecutando script de Python: $PYTHON_SCRIPT..." > "$LOG_FILE"
"$VENV_DIR/bin/python" "$PYTHON_SCRIPT" 2>>"$ERR_FILE" > "$LOG_FILE"

# Desactivar el entorno virtual
deactivate

# Verificar si hubo errores y reportar
if [ -s "$ERR_FILE" ]; then
  echo "Error en forumToEmail.sh. Verifique el archivo de error: $ERR_FILE" > "$LOG_FILE"
  cat "$ERR_FILE" > "$LOG_FILE" # También registrar los errores en el log principal
else
  echo "forumToEmail.sh finalizado sin errores." > "$LOG_FILE"
fi

echo "Log completo en $LOG_FILE" > "$LOG_FILE"
echo "Errores (si los hay) en $ERR_FILE" > "$LOG_FILE"

