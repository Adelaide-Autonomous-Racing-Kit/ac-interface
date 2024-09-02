#!/bin/bash
AC_PATH="$HOME/.cxoffice/Assetto_Corsa/drive_c/Program Files (x86)/Steam/steamapps/common/assettocorsa/";
cd "$AC_PATH";

while true;
    do 
    READ="$(cat $HOME/named_pipes/aci_execution_pipe)";
    echo $READ;

    # Cross Over Options
    if [ "$READ" = "launch_ac_crossover" ]; then
        bash -c "/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app acs.exe" &> $HOME/named_pipes/aci_execution_output.txt;
        echo "Launched Assetto Corsa";
    elif [ "$READ" = "shutdown_ac_crossover" ]; then
        killall "acs.exe";
        echo "Shutdown Assetto Corsa"
    elif [ "$READ" = "launch_server_crossover" ]; then
        bash -c "echo python -m acs.server | /opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe" &
        SERVER_PID=$!;
    elif [ "$READ" = "shutdown_server_crossover" ]; then
        # This gets the wrong PID currently
        kill $SERVER_PID;
    # Proton Options
    elif [ "$READ" = "launch_ac_proton" ]; then
        bash scripts/run_ac.sh
    elif [ "$READ" = "shutdown_ac_proton" ]; then
        killall "AssettoCorsa.ex";
    elif [ "$READ" = "shutdown_server_proton" ]; then
        killall "ac-state.exe";
    # Terminate pipe
    elif [ "$READ" = "shutdown_aci_execution_pipe" ]; then
        break
    fi
done
