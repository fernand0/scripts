#!/bin/sh
# Salir inmediatamente si un comando falla.
set -e

# Nombre del script: argumento posicional o variable de entorno SCRIPT_NAME
SCRIPT_NAME="${1:-$SCRIPT_NAME}"
if [ -z "$SCRIPT_NAME" ]; then
  echo "Uso: $0 <nombre_script>  (o define la variable de entorno SCRIPT_NAME)"
  exit 1
fi

# Buscar el archivo de error más reciente del script indicado
LATEST_ERROR_FILE=$(ls -t /tmp/${SCRIPT_NAME}_error_*.log 2>/dev/null | head -n 1)

# Comprobar si se encontró un archivo Y si tiene contenido
if [ -n "$LATEST_ERROR_FILE" ] && [ -s "$LATEST_ERROR_FILE" ]; then
  echo "Iniciando size.sh para verificar errores de $SCRIPT_NAME..."
  echo "Se encontró el archivo de error más reciente: $LATEST_ERROR_FILE"
  echo "Contenido del error:"
  cat "$LATEST_ERROR_FILE"
  echo "Fin del contenido del error."
  echo "size.sh finalizado."
fi
