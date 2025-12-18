#!/bin/sh
# Salir inmediatamente si un comando falla.
set -e

# Definir variables para facilitar la configuración
VENV_DIR="$HOME/.clean"
PYTHON_SCRIPT="/home/ftricas/usr/src/Python/moveMailImap.py"
DEPS="social-modules @ git+https://github.com/fernand0/socialModules.git"
LANZADOR_SCRIPT="/home/ftricas/usr/src/scripts/lanzador.sh"

echo "Iniciando cleanImap.sh..."

# Crear el entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
  echo "El entorno virtual no existe. Creándolo en $VENV_DIR..."
  uv venv "$VENV_DIR"
  echo "Entorno creado."
fi

# Ejecutar el script de Python usando lanzador.sh
"$LANZADOR_SCRIPT" \
    --venv "$VENV_DIR" \
    --deps "$DEPS" \
    cleanImap \
    "$PYTHON_SCRIPT"

echo "cleanImap.sh finalizado."
