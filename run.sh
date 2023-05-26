#!/bin/bash
# Initialize parameters
hostID="1234567890"
server=""
while (( "$#" )); do
  if [[ $1 == "--hostID" ]]; then
    hostID="$2"
    shift 2
  elif [[ $1 == "--server" ]]; then
    server="-h $2"
    shift 2
  else
    shift
  fi
done
cp mixer.sh mixer_$hostID.sh
#sed -i "s/hostID=\"\"/hostID=\"$hostID\"/g" "$hostID.sh"
perl -pi -e "s/hostID=\"\"/hostID=\"$hostID\"/g" "mixer_$hostID.sh"
chmod +x mixer_$hostID.sh
## Including mixer breaks the audio stream :/
## TODO: Fix that shit
snapclient $server --logsink file:run.log --player file  --sampleformat 44100:16:* --hostID $hostID $@ | ffmpeg -hide_banner -f u16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 pipe:1 
# snapclient $server --logsink file:run.log --player file  --sampleformat 44100:16:* --mixer script:./mixer_$hostID.sh --hostID $hostID $@ | ffmpeg -hide_banner -f u16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 pipe:1 
# snapclient $server --logsink file:run.log --player file  --sampleformat 44100:16:* --mixer script:./mixer_$hostID.sh --hostID $hostID $@ | ffmpeg -hide_banner -f u16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 pipe:1 > $hostID.mp3
# snapclient $server --logsink file:run.log --player file:filename=stdout  --sampleformat 44100:16:* --mixer script:./mixer_$hostID.sh --hostID $hostID $@ | ffmpeg -hide_banner -loglevel error -f s16le -acodec pcm_s16le -ac 2 -ar 44100 -i pipe:0 -f mp3 -q:a 2 pipe:1 > $hostID.mp3

