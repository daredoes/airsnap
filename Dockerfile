FROM ghcr.io/postlund/pyatv:master

RUN apk add git snapcast perl ffmpeg bash curl
COPY requirements.txt /
RUN pip uninstall -y pyatv && pip install -r /requirements.txt
COPY web.py /
COPY main.py /
COPY run.sh /
COPY mixer.sh /
RUN chmod +x main.py run.sh web.py mixer.sh
ENV PORT=8080
ENV SNAPCAST_SERVER=snapcast.local
ENTRYPOINT ["python", "/web.py"]