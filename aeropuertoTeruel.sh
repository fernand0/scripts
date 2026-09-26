#!/bin/bash
"$(dirname "$0")/lanzador.sh" \
    --deps 'FlightRadarAPI "social-modules @ git+https://github.com/fernand0/socialModules.git"' \
    --args "TEV" \
    aeropuertoTeruel \
    "$HOME/usr/src/Python/testingFlightRadar.py"
