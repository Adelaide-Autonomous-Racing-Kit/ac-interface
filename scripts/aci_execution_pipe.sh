#!/bin/bash
AC_PATH="$HOME/.cxoffice/Assetto_Corsa/drive_c/Program Files (x86)/Steam/steamapps/common/assettocorsa/";
cd "$AC_PATH";

while true;
    do 
    READ="$(cat $HOME/named_pipes/aci_execution_pipe)";
    echo $READ
    if [ $READ=='launch_assetto_corsa' ]; then
    eval "/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app acs.exe" &> $HOME/named_pipes/aci_execution_output.txt;
    fi
    if [ $READ=='launch_state_server' ]; then
    eval "echo python -m aci.game_capture.state.server | /opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe" &
    fi
done