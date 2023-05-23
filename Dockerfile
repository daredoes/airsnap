FROM ghcr.io/postlund/pyatv:master

RUN apk add git
COPY requirements.txt /
COPY web.py /
RUN chmod +x web.py
COPY main.py /
RUN chmod +x main.py
COPY run.sh /
RUN chmod +x run.sh
COPY mixer.sh /
RUN chmod +x mixer.sh
RUN pip install -r /requirements.txt
ENTRYPOINT ["python", "/web.py"]