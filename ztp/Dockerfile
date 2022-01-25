FROM python:3.9.5-slim-buster
LABEL net.juniper.vendor "Juniper Networks"
LABEL description "ztp automation"
LABEL maintainer="Joe Alphonso <jalphonso@juniper.net>" \
      version="1.3"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /root

ENV PATH="/root/.local/bin:${PATH}"

COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY ztp .

EXPOSE 5000

CMD ["gunicorn", "--workers", "5", "--bind", ":5000", "--worker-tmp-dir", "/dev/shm", "wsgi:app"]
