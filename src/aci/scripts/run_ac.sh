#!/bin/bash
export WINEPREFIX=$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx
export STEAM_COMPAT_DATA_PATH=$HOME/.local/share/Steam/steamapps/compatdata/244210
export STEAM_COMPAT_CLIENT_INSTALL_PATH=$HOME/.steam/steam/
export PROTON_REMOTE_DEBUG_CMD="$HOME/.local/share/Steam/steamapps/common/assettocorsa/ac-state.exe"

cd $HOME/.local/share/Steam/steamapps/common/assettocorsa
$HOME/.local/share/Steam/compatibilitytools.d/GE-Proton9-2/proton waitforexitandrun acs.exe