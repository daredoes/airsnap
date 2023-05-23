#!/bin/bash
snapclient -h 192.168.1.104  --logsink file:run.log --sampleformat 44100:16:* --latency 10 $@