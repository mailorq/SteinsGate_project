FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app


RUN apk update && \
    apk add --update --no-cache \
    libpq \
    jpeg-dev \
    zlib-dev \
    libwebp-dev \
    freetype-dev \
    libffi-dev \
    --virtual .build-deps \
    build-base \
    postgresql-dev \
    musl-dev \
    linux-headers

ARG user=django-user
ARG uid=1000
ARG gid=1000

RUN addgroup -g $gid $user && \
    adduser -D -u $uid -G $user $user

RUN mkdir -p /app/static /app/media && \
    chown -R $user:$user /app

COPY --chown=$user:$user ./requirements.txt ./requirements.txt

USER $user

ENV PATH="/home/$user/.local/bin:/usr/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY --chown=$user:$user . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]