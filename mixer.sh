#!/bin/bash

# Initialize parameters
hostID=""
volume=""
mute=""

# Parse command line parameters
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --volume) volume="$2"; shift ;;
        --mute) mute="$2"; shift ;;
        *) echo "Unknown parameter passed: $1" >> $hostID.log; exit 1 ;;
    esac
    shift
done

# Check if parameters are set
if [[ -z "$volume" || -z "$mute" ]]; then
    echo "Parameters --volume and --mute are required." >> $hostID.log
    exit 1
fi

# If mute is true, set volume to 0
if [[ "$mute" == "true" ]]; then
    volume=0
fi

volume=$(echo "scale=0; $volume * 100 / 1" | bc)

# Adjust this URL based on your requirements
curl -s -o /dev/null "http://localhost:8080/$hostID/$volume"
