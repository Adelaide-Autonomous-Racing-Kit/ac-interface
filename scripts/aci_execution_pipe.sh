#!/bin/bash
AC_PATH="$HOME/.cxoffice/Assetto_Corsa/drive_c/Program Files (x86)/Steam/steamapps/common/assettocorsa";

while true;
    do 
    READ="$(cat $HOME/named_pipes/aci_execution_pipe)";
    echo $READ;

    # Cross Over Options
    if [ "$READ" = "crossover_launch_ac" ]; then
        bash -c "/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app $AC_PATH/acs.exe" &> $HOME/named_pipes/aci_execution_output.txt;
        echo "Launched Assetto Corsa";
    elif [ "$READ" = "crossover_shutdown_ac" ]; then
        killall "acs.exe";
        echo "Shutdown Assetto Corsa"
    elif [ "$READ" = "crossover_launch_server" ]; then
        bash -c "echo python -m acs.server | /opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe" &
    elif [ "$READ" = "crossover_shutdown_server" ]; then
        # This gets the wrong PID currently
        kill $SERVER_PID;
    # Proton Options
    elif [ "$READ" = "proton_launch_ac" ]; then
        echo "Trying to launch"
        bash scripts/run_ac.sh
        echo "Maybe it launched?"
    elif [ "$READ" = "proton_shutdown_ac" ]; then
        killall "AssettoCorsa.ex";
    elif [ "$READ" = "proton_shutdown_server" ]; then
        killall "ac-state.exe";
    # Terminate pipe
    elif [ "$READ" = "shutdown_aci_execution_pipe" ]; then
        killall "acs.exe";
        killall "AssettoCorsa.ex";
        killall "ac-state.exe";
        break
    fi
done