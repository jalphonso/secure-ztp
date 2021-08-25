FROM python:3.9.5-slim-buster
LABEL net.juniper.vendor "Juniper Networks"
LABEL description "ztp automation"
LABEL maintainer="Joe Alphonso <jalphonso@juniper.net>" \
      version="1.2"

RUN useradd -m ztp
USER ztp
WORKDIR /home/ztp

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV PATH="/home/ztp/.local/bin:${PATH}"

COPY --chown=ztp:ztp requirements.txt .
RUN pip install --user -r requirements.txt
COPY --chown=ztp:ztp ztp .

EXPOSE 5000

CMD ["gunicorn", "--workers", "5", "--bind", ":5000", "--worker-tmp-dir", "/dev/shm", "wsgi:app"]
