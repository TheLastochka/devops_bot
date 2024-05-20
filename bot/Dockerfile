FROM python:3.10-alpine
WORKDIR /bot

RUN mkdir -p logs
COPY requirements.txt requirements.txt
RUN \
    apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    python3 -m pip install -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps
COPY . .

CMD ["python", "bot.py"]

