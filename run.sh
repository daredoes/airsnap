#!/bin/bash
# Initialize parameters
hostID=""
while (( "$#" )); do
  if [[ $1 == "--hostID" ]]; then
    hostID="$2"
    shift 2
  else
    shift
  fi
done
cp mixer.sh $hostID.sh
#sed -i "s/hostID=\"\"/hostID=\"$hostID\"/g" "$hostID.sh"
perl -pi -e "s/hostID=\"\"/hostID=\"$hostID\"/g" "$hostID.sh"

chmod +x $hostID.sh
snapclient -h 192.168.1.104 --logsink null --player file  --sampleformat 44100:16:* --mixer script:./$hostID.sh --hostID $hostID $@ | ffmpeg -f u16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 pipe:1 