#!/bin/bash
# xserver permissions for docker
xhost +local:docker
# Setup named pipe for host process execution
if ! test -p $HOME/named_pipes/aci_execution_pipe; then
    mkdir $HOME/named_pipes
    mkfifo $HOME/named_pipes/aci_execution_pipe
fi
bash scripts/aci_execution_pipe.sh &> /dev/null &