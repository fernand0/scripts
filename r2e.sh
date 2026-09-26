#!/bin/bash
set -e

VENV_DIR="$HOME/.socialBots"

# Crear el entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
  echo "El entorno virtual '$VENV_DIR' no existe. Creándolo..."
  uv venv "$VENV_DIR"
fi

# Instalar/actualizar r2e
uv pip install --python "$VENV_DIR/bin/python" rss2email

# Ejecutar r2e
"$VENV_DIR/bin/r2e" run
