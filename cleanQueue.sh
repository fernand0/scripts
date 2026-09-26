#!/bin/sh
# Salir inmediatamente si un comando falla.

# set -x
set -e

# Definir variables para facilitar la configuración
VENV_DIR="$HOME/.clean"
PYTHON_SCRIPT="$HOME/usr/src/Python/cleaningQueue.py"
LOG_FILE="/tmp/cleanQueue_$(date +%Y%m%d_%H%M%S).log"
REPO_URL="social-modules @ git+https://github.com/fernand0/socialModules.git@devel"

echo "Iniciando cleanQueue.sh..."

# Crear el entorno virtual e instalar dependencias si no existe
if [ ! -d "$VENV_DIR" ]; then
  echo "El entorno virtual no existe. Creándolo en $VENV_DIR..."
  uv venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  echo "Instalando dependencias..."
  uv pip install "$REPO_URL"
  deactivate
  echo "Entorno creado y configurado."
fi

# Activar el entorno y ejecutar el script
echo "Activando entorno y ejecutando el script de Python..."
source "$VENV_DIR/bin/activate"
which python
which uv
uv run --active python "$PYTHON_SCRIPT" 2>&1 | tee "$LOG_FILE"
deactivate

echo "cleanQueue.sh finalizado. Log guardado en $LOG_FILE"
