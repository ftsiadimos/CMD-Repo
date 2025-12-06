FROM python:3.12-slim AS builder
COPY . /app
WORKDIR /app
#RUN dnf install pip -y
RUN pip install -r requirements.txt
CMD ["/usr/local/bin/gunicorn", "-b", ":5001", "app:app"]
#CMD ["flask", "run"]