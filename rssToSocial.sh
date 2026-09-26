#!/bin/bash
"$(dirname "$0")/lanzador.sh" \
    --deps "social-modules@git+https://github.com/fernand0/socialModules.git" \
    "rssToSocial" \
    "$HOME/.socialBots/lib/python3.12/site-packages/socialModules/moduleRules.py"
