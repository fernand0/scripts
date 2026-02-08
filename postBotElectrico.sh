#!/bin/bash
# Salir inmediatamente si un comando falla.
set -e

home_bot="$HOME/usr/src/Python/deGitHub/botElectrico/"
posts="docs/_posts/"

echo "Iniciando postBotElectrico.sh..."

# Cambiar al directorio del repositorio
cd "$home_bot" || { echo "Error: No se pudo cambiar al directorio del repositorio: $home_bot"; exit 1; }

# Verificar si es un repositorio Git
if [ ! -d ".git" ]; then
  echo "Error: El directorio $home_bot no es un repositorio Git."
  exit 1
fi

# Obtener la fecha actual en el formato "aaa-mm-dd"
fecha_actual=$(date +%Y-%m-%d)

# Ruta del archivo en /tmp
archivo_tmp="/tmp/$fecha_actual-post.md"

# Ruta del directorio de destino
directorio_destino="$home_bot$posts"

# Comprobar si el archivo existe en /tmp
if [ -f "$archivo_tmp" ]; then
  echo "Archivo temporal encontrado: $archivo_tmp"

  # Guardar la rama actual para volver a ella al final
  current_branch=$(git rev-parse --abbrev-ref HEAD)
  echo "Rama actual: $current_branch"

  # Mover el archivo al directorio de destino
  echo "Cambiando a la rama gh-pages..."
  git checkout gh-pages || { echo "Error: No se pudo cambiar a la rama gh-pages."; exit 1; }

  echo "Moviendo $archivo_tmp a $directorio_destino..."
  mv "$archivo_tmp" "$directorio_destino" || { echo "Error: No se pudo mover el archivo."; exit 1; }
  echo "Archivo movido."

  echo "Realizando git pull en gh-pages..."
  git pull || { echo "Advertencia: git pull falló en gh-pages. Intentando continuar..."; } # Pull puede fallar por red, no es crítico para el commit

  echo "Añadiendo cambios a Git..."
  git add "$directorio_destino" || { echo "Error: No se pudo añadir el directorio al staging."; exit 1; }

  echo "Realizando commit..."
  git commit -am"Post: $fecha_actual" || { echo "Advertencia: No hay cambios para commitear o commit falló."; } # Commit puede fallar si no hay cambios

  echo "Realizando git push..."
  git push || { echo "Error: git push falló. Verifique sus credenciales y conexión."; exit 1; }

  echo "Volviendo a la rama original ($current_branch)..."
  git checkout "$current_branch" || { echo "Error: No se pudo volver a la rama original."; exit 1; }

  echo "Proceso de publicación completado para $fecha_actual."
else
  echo "No se encontró el archivo $archivo_tmp en /tmp. No hay post para publicar."
fi

echo "postBotElectrico.sh finalizado."