#!/bin/bash
/home/ftricas/usr/src/scripts/lanzador.sh \
    --deps 'FlightRadarAPI "social-modules @ git+https://github.com/fernand0/socialModules.git"' \
    --args "TEV" \
    aeropuertoTeruel \
    "$HOME/usr/src/Python/testingFlightRadar.py"
