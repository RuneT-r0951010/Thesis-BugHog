FROM python:3.11-slim-buster AS base

WORKDIR /app

RUN apt-get update -y
RUN apt install -y curl gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils libgbm-dev xvfb dbus-x11 libnss3-tools python3-pip vim multiarch-support wget git procps \
 && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://get.docker.com/ | sh

# Stuff needed for chrome versions < 40
RUN wget -O libgcrypt11.deb https://launchpadlibrarian.net/201289896/libgcrypt11_1.5.3-2ubuntu4.2_amd64.deb &&\
    wget -O libudev0.deb https://launchpad.net/ubuntu/+source/udev/175-0ubuntu9/+build/3386050/+files/libudev0_175-0ubuntu9_amd64.deb &&\
    wget -O libpng12.deb http://mirrors.kernel.org/ubuntu/pool/main/libp/libpng/libpng12-0_1.2.54-1ubuntu1_amd64.deb &&\
    dpkg -i libgcrypt11.deb &&\
    dpkg -i libudev0.deb &&\
    dpkg -i libpng12.deb &&\
    rm libgcrypt11.deb &&\
    rm libudev0.deb &&\
    rm libpng12.deb

# Stuff needed for chrome versions < 17
RUN ln -s /usr/lib/x86_64-linux-gnu/libnss3.so /usr/lib/x86_64-linux-gnu/libnss3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libnssutil3.so /usr/lib/x86_64-linux-gnu/libnssutil3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libsmime3.so /usr/lib/x86_64-linux-gnu/libsmime3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libssl3.so /usr/lib/x86_64-linux-gnu/libssl3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libplds4.so /usr/lib/x86_64-linux-gnu/libplds4.so.0d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libplc4.so /usr/lib/x86_64-linux-gnu/libplc4.so.0d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libnspr4.so /usr/lib/x86_64-linux-gnu/libnspr4.so.0d

# Create user `bci`
RUN useradd -m bci && \
    # Grant access to docker
    usermod -aG docker bci && \
    newgrp docker && \
    touch /var/run/docker.sock && \
    chown bci:bci /var/run/docker.sock && \
    # Make owner of folders it has to write in
    mkdir -p /app/logs && \
    mkdir -p /app/binaries/chromium/downloaded && \
    mkdir -p /app/binaries/firefox/downloaded && \
    mkdir -p /app/binaries/chromium/artisanal && \
    mkdir -p /app/binaries/firefox/artisanal && \
    chown -R bci:bci /app && \
    chown bci:bci /app/logs && \
    chown -R bci:bci /app/binaries/chromium/ && \
    chown -R bci:bci /app/binaries/firefox/

COPY --chown=bci:bci resources/profiles/ /app/profiles/

# Add xvfb service
RUN echo "Xvfb :1 -screen 0 1024x768x16 &" > /etc/init.d/xvfb && \
    chmod +x "/etc/init.d/xvfb"


USER bci

# Install python packages
COPY requirements.txt /app/requirements.txt
RUN  python3 -m pip install -r /app/requirements.txt


################
# Certificates #
################

# Commented part below was used for mitmproxy
# COPY --chown=bci:bci ./bci/proxy/ca_generator.py /home/bci/ca_generator.py
# # Generate certificates
# RUN mkdir -p /home/bci/.mitmproxy/ && \
#     python /home/bci/ca_generator.py /home/bci/.mitmproxy/mitmproxy-ca.pem /home/bci/.mitmproxy/mitmproxy-ca.crt && \

COPY --chown=bci:bci resources/ssl/bughog_ca.crt /home/bci/bughog_ca.crt
# Add certificates to Chromium
RUN mkdir -p $HOME/.pki/nssdb && \
    certutil -d sql:$HOME/.pki/nssdb -A -t TC -n bci-ca -i /home/bci/bughog_ca.crt && \
# Add certificates to Firefox
# Legacy se rity databases (cert8.db and key3.db)
    certutil -A -n bci-ca -t CT,c -i /home/bci/bughog_ca.crt -d /app/profiles/firefox/default-67/ && \
    certutil -A -n bci-ca -t CT,c -i /home/bci/bughog_ca.crt -d /app/profiles/firefox/tp-67/ && \
# New SQL security databases (cert9.db and key4.db)
    certutil -A -n bci-ca -t CT,c -i /home/bci/bughog_ca.crt -d sql:/app/profiles/firefox/default-67/ && \
    certutil -A -n bci-ca -t CT,c -i /home/bci/bughog_ca.crt -d sql:/app/profiles/firefox/tp-67/
# # More info: https://support.mozilla.org/en-US/questions/1207165
# #cp firefox/cert8.db firefox/default-67/ &&\
# #cp firefox/cert8.db firefox/tp-67/

# # mitmproxy configuration
# RUN echo "tls_version_client_min: UNBOUND" > /home/bci/.mitmproxy/config.yaml && \
#     echo "tls_version_server_min: UNBOUND" >> /home/bci/.mitmproxy/config.yaml && \
#     echo "listen_port: 8081" >> /home/bci/.mitmproxy/config.yaml

# Copy environment variables
COPY --chown=bci:bci --chmod=0755 resources/scripts/bci/* /app/


FROM base AS core
# Copy rest of source code
COPY --chown=bci:bci bci /app/bci
COPY --chown=bci:bci analysis /app/analysis
USER root
ENTRYPOINT [ "/app/core.sh" ]

FROM base AS worker
# Copy rest of source code
COPY --chown=bci:bci bci /app/bci
ENTRYPOINT [ "/app/worker.sh" ]