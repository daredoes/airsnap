#!/bin/bash
# snapclient -h 192.168.1.104 --logsink file:run.log --player file:stdout --sampleformat 48000:16:* $@ | ffmpeg -f u16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 pipe:1 
# this is best 3-4 seconds lag
printenv > test.log
snapclient -h 192.168.1.104 --logsink null --player file  --sampleformat 44100:16:* $@ | ffmpeg -f u16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 pipe:1 
# this is okay 12 seconds
# snapclient -h 192.168.1.104 --player stdout --logsink file:run.log --sampleformat 44100:16:* $@ | ffmpeg -f s16le -ar 44100 -ac 2 -i pipe:0 -f mp3 pipe:1 