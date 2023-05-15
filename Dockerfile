FROM ghcr.io/postlund/pyatv:master

COPY web.py /
RUN chmod +x web.py
ENTRYPOINT ["python", "/web.py"]