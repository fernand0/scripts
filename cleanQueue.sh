#!/bin/bash
# Crear el entorno virtual si no existe
VENV_DIR="$HOME/.clean"
if [ ! -d "$VENV_DIR" ]; then
  echo "El entorno virtual no existe. Creándolo en $VENV_DIR..."
  uv venv "$VENV_DIR"
fi

"$(dirname "$0")/lanzador.sh" \
    --venv "$VENV_DIR" \
    --deps "social-modules @ git+https://github.com/fernand0/socialModules.git" \
    cleanQueue \
    "$HOME/usr/src/Python/cleaningQueue.py"
