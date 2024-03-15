#!/bin/bash

# Lista todos os processos zombis e tenta terminá-los
for pid in $(ps -A -ostat,ppid,pid,comm | awk '/^Z/ {print $3}'); do
    kill -9 $pid 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Zombie process $pid was terminated."
    else
        echo "Failed to terminate zombie process $pid."
    fi
done
