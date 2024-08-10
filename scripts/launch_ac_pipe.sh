#!/bin/bash
AC_PATH="$HOME/.cxoffice/Assetto_Corsa/drive_c/Program Files (x86)/Steam/steamapps/common/assettocorsa/";
cd "$AC_PATH";

while true;
    do 
    READ="$(cat $HOME/named_pipes/ac_launch_pipe)";
    echo $READ
    if [ $READ=='launch' ]; then
    eval "/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app acs.exe" &> $HOME/named_pipes/ac_exec_pipe_output.txt;
    fi
done