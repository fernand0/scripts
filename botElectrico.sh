#!/bin/bash
/home/ftricas/usr/src/scripts/lanzador.sh \
    --deps matplotlib \
    --deps "social-modules@git+https://github.com/fernand0/socialModules.git" \
    --deps plotly \
    --deps pandas \
    --post-script "$HOME/usr/src/scripts/postBotElectrico.sh" \
    "botElectrico" \
    "$HOME/usr/src/Python/deGitHub/botElectrico/botElectrico.py"
#    --args "-s" \
