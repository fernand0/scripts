#!/bin/bash
/home/ftricas/usr/src/scripts/lanzador.sh \
    --deps "social-modules@git+https://github.com/fernand0/socialModules.git" \
    --post-script "$HOME/usr/bin/size.sh" \
    "rssToSocial" \
    "$HOME/.socialBots/lib/python3.12/site-packages/socialModules/moduleRules.py"
