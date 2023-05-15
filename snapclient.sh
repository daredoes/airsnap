#!/bin/bash
snapclient -h 192.168.1.104 --player file --logsink null $@ | ffmpeg -f s16le -ar 44100 -ac 2 -i pipe:0 -f mp3 pipe:1