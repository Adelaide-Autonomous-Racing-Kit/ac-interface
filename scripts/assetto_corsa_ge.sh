#!/bin/bash

# winetricks: dotnet40 dotnet452 d3dx11_43 d3dcompiler_47
curl -LO https://github.com/GloriousEggroll/proton-ge-custom/releases/download/GE-Proton9-2/GE-Proton9-2.tar.gz
mkdir ~/.steam/root/compatibilitytools.d
tar -xf GE-Proton9-2.tar.gz -C ~/.steam/root/compatibilitytools.d/
rm GE-Proton9-2.tar.gz

