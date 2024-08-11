#!/bin/bash
AC_PATH="$HOME/.cxoffice/Assetto_Corsa/drive_c/Program Files (x86)/Steam/steamapps/common/assettocorsa/";
cd "$AC_PATH";

while true;
    do 
    READ="$(cat $HOME/named_pipes/aci_execution_pipe)";
    echo $READ;

    if [ "$READ" = "launch_assetto_corsa" ]; then
        bash -c "/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app acs.exe" &> $HOME/named_pipes/aci_execution_output.txt;
        echo "Launched Assetto Corsa";
    elif [ "$READ" = "shutdown_assetto_corsa" ]; then
        killall "acs.exe";
        echo "Shutdown Assetto Corsa"
    elif [ "$READ" = "launch_state_server" ]; then
        bash -c "echo python -m aci.game_capture.state.server | /opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe" &
        SERVER_PID=$!;
    elif [ "$READ" = "shutdown_state_server" ]; then
        # This gets the wrong PID currently
        kill $SERVER_PID;
        echo "Shutdown State Server"
    elif [ "$READ" = "shutdown_aci_execution_pipe" ]; then
        break
    fi
done
