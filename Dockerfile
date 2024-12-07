FROM python:3.11-alpine

WORKDIR /usr/src/app

COPY . /usr/src/app/
RUN apk update && apk add gcc musl-dev librdkafka-dev \
&& pip install --no-cache-dir -r requirements.txt \
&& apk del gcc musl-dev

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]