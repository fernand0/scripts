#!/bin/bash
"$(dirname "$0")/lanzador.sh" \
    --deps "requests beautifulsoup4" \
    rssComic \
    "$HOME/usr/src/Python/comicsRss.py"
