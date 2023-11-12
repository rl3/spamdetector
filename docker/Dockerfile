FROM debian:bookworm

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        git \
        python3 \
        python3-venv \
        pip \
        && \
    apt-get clean

RUN git clone https://github.com/rl3/spamdetector.git

RUN cd /spamdetector; python3 -m venv .venv; . .venv/bin/activate; pip install -r requirements.txt

# COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY start.sh /usr/local/bin/start.sh
RUN chmod 755 /usr/local/bin/*.sh

# ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

EXPOSE 10025/tcp

CMD ["/usr/local/bin/start.sh"]
