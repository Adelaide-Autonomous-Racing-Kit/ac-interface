#!/bin/bash
export WINEPREFIX=$HOME/.local/share/Steam/steamapps/compatdata/244210/pfx
export STEAM_COMPAT_DATA_PATH=$HOME/.local/share/Steam/steamapps/compatdata
export STEAM_COMPAT_CLIENT_INSTALL_PATH=$HOME/.steam/steam/

cd $HOME/.local/share/Steam/steamapps/common/assettocorsa
# Swap client and launcher name
if ! test -f AssettoCorsa_1.exe; then
    mv AssettoCorsa.exe AssettoCorsa_1.exe
    mv acs.exe AssettoCorsa.exe
fi

$HOME/.local/share/Steam/compatibilitytools.d/GE-Proton9-2/proton run AssettoCorsa.exe &

sleep 20s

# Swap back client and launcher name
mv ./AssettoCorsa.exe ./acs.exe
mv ./AssettoCorsa_1.exe ./AssettoCorsa.exe