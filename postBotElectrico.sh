#!/bin/bash
set -e

home_bot="$HOME/usr/src/Python/deGitHub/botElectrico"
posts="docs/_posts/"
fecha_actual=$(date +%Y-%m-%d)
archivo_tmp="/tmp/$fecha_actual-post.md"
directorio_destino="$home_bot/$posts"

if [ ! -f "$archivo_tmp" ]; then
  echo "No se encontró el archivo $archivo_tmp. No hay post para publicar."
  exit 0
fi

cd "$home_bot"
current_branch=$(git rev-parse --abbrev-ref HEAD)

git checkout gh-pages
mv "$archivo_tmp" "$directorio_destino"
git pull || true
git add "$directorio_destino"
git commit -am"Post: $fecha_actual" || true
git push
git checkout "$current_branch"
