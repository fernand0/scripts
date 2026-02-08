#!/bin/bash
# Salir inmediatamente si un comando falla.
set -e

# Función para restaurar la rama original en caso de error
restore_branch() {
    if [ -n "$original_branch" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Restaurando rama original: $original_branch"
        git checkout "$original_branch" 2>/dev/null || echo "$(date '+%Y-%m-%d %H:%M:%S') - Error al restaurar la rama original"
    fi
}

# Configurar trap para restaurar la rama original en caso de error
trap restore_branch ERR

# Directorios configurables
home_bot="${BOT_HOME:-$HOME/usr/src/Python/deGitHub/botElectrico/}"
posts="docs/_posts/"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Iniciando postBotElectrico.sh..."

# Cambiar al directorio del repositorio
cd "$home_bot" || { echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: No se pudo cambiar al directorio del repositorio: $home_bot"; exit 1; }

# Verificar si es un repositorio Git
if [ ! -d ".git" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: El directorio $home_bot no es un repositorio Git."
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
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Archivo temporal encontrado: $archivo_tmp"
  
  # Verificar que el archivo tenga contenido
  if [ ! -s "$archivo_tmp" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Advertencia: El archivo $archivo_tmp está vacío. No se procesará."
    exit 0
  fi

  # Guardar la rama actual para volver a ella al final
  original_branch=$(git rev-parse --abbrev-ref HEAD)
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Rama actual: $original_branch"

  # Verificar que la rama gh-pages existe
  if ! git rev-parse --verify gh-pages >/dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: La rama gh-pages no existe."
    exit 1
  fi

  # Mover el archivo al directorio de destino
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Cambiando a la rama gh-pages..."
  git checkout gh-pages || { echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: No se pudo cambiar a la rama gh-pages."; exit 1; }

  echo "$(date '+%Y-%m-%d %H:%M:%S') - Moviendo $archivo_tmp a $directorio_destino..."
  mv "$archivo_tmp" "$directorio_destino" || { echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: No se pudo mover el archivo."; exit 1; }
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Archivo movido."

  echo "$(date '+%Y-%m-%d %H:%M:%S') - Realizando git pull en gh-pages..."
  if ! git pull origin gh-pages; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Advertencia: git pull falló en gh-pages. Intentando continuar..."
  fi

  echo "$(date '+%Y-%m-%d %H:%M:%S') - Añadiendo cambios a Git..."
  git add "$directorio_destino" || { echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: No se pudo añadir el directorio al staging."; exit 1; }

  # Solo hacer commit si hay cambios
  if git diff --cached --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No hay cambios para commitear."
  else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Realizando commit..."
    if git commit -m"Post: $fecha_actual"; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Commit realizado correctamente."
      
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Realizando git push..."
      if git push origin gh-pages; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Push realizado correctamente."
      else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: git push falló. Verifique sus credenciales y conexión."
        git checkout "$original_branch"  # Restaurar antes de salir
        exit 1
      fi
    else
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: Falló el commit."
      git checkout "$original_branch"  # Restaurar antes de salir
      exit 1
    fi
  fi

  echo "$(date '+%Y-%m-%d %H:%M:%S') - Volviendo a la rama original ($original_branch)..."
  git checkout "$original_branch" || { echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: No se pudo volver a la rama original."; exit 1; }

  echo "$(date '+%Y-%m-%d %H:%M:%S') - Proceso de publicación completado para $fecha_actual."
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') - No se encontró el archivo $archivo_tmp en /tmp. No hay post para publicar."
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - postBotElectrico.sh finalizado."