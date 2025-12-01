FROM postgres:16

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        wget \
        postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/pgvector \
    && cd /tmp/pgvector \
    && wget https://github.com/pgvector/pgvector/archive/refs/tags/v0.7.4.tar.gz \
    && tar -xzf v0.7.4.tar.gz \
    && cd pgvector-0.7.4 \
    && make \
    && make install \
    && cd / \
    && rm -rf /tmp/pgvector
