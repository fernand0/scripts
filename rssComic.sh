#!/bin/bash

/home/ftricas/usr/bin/lanzador.sh \
    --deps "requests beautifulsoup4" \
    "rssComic" \
    "/home/ftricas/usr/src/Python/comicsRss.py" > /tmp/rssComic.log
