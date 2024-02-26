# Use a imagem base do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie apenas o arquivo de requisitos para aproveitar o cache
COPY requirements.txt .

# Instale os pacotes necessários, Chromium, chromedriver, libffi-dev, curl, pkg-config e libssl-dev
RUN apt-get update -qqy \
    && apt-get install -qqy curl chromium chromium-driver libffi-dev pkg-config libssl-dev tigervnc-standalone-server \
    tigervnc-common xvfb lxde\
    libx11-6 libx11-xcb1 libfontconfig1 libfreetype6 libxext6 libxrender1 libxtst6 libnss3 libnspr4 libasound2 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Instale as dependências do projeto Python
RUN pip install -r requirements.txt

# Copie o restante dos arquivos do projeto para o diretório de trabalho
COPY . .

ARG VNC_PASSWORD
# Defina a senha do VNC
RUN mkdir ~/.vnc \
    && echo $VNC_PASSWORD | vncpasswd -f > ~/.vnc/passwd \
    && chmod 600 ~/.vnc/passwd