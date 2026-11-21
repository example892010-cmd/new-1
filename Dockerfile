FROM python:3.11.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /bot

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        jq \
        mediainfo \
        pv \
        wget \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

CMD ["bash", "run.sh"]
