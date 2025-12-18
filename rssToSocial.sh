#!/bin/bash
$HOME/usr/bin/lanzador.sh \
    --deps "social-modules @ git+https://github.com/fernand0/socialModules.git" \
    --post-script "$HOME/usr/bin/size.sh" \
    "rssToSocial" \
    "$HOME/.socialBots/lib/python3.11/site-packages/socialModules/moduleRules.py"
