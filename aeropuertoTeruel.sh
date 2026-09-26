#!/bin/sh
# Delega en lanzador.sh toda la lógica de entorno virtual, dependencias y logs.

LANZADOR="$(dirname "$0")/lanzador.sh"
SIZE_SH="$(dirname "$0")/size.sh"

PYTHON_SCRIPT="$HOME/usr/src/Python/testingFlightRadar.py"
DEPS='FlightRadarAPI "social-modules @ git+https://github.com/fernand0/socialModules.git"'
ARGUMENT="TEV"

"$LANZADOR" \
  --deps "$DEPS" \
  --args "$ARGUMENT" \
  --post-script "$SIZE_SH" \
  aeropuertoTeruel \
  "$PYTHON_SCRIPT"
