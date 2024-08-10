#!/bin/bash

while true;
    do 
    READ="$(cat $HOME/named_pipes/state_server_pipe)";
    if [ $READ=='start' ]; then
    eval "echo python -m aci.game_capture.state.server | /opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe" &
    fi
done