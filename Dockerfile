# Use a imagem base do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos do projeto para o diretório de trabalho
COPY . /app

# Instale os pacotes necessários, Chromium, chromedriver, libffi-dev, curl, pkg-config e libssl-dev
RUN apt-get update -qqy \
  && apt-get install -qqy curl chromium chromium-driver libffi-dev pkg-config libssl-dev xvfb gcc python3-dev \
  libx11-6 libx11-xcb1 libfontconfig1 libfreetype6 libxext6 libxrender1 libxtst6 libnss3 libnspr4 libasound2 \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Instale as dependências do projeto Python
RUN pip install -r requirements.txt

# Defina o comando a ser executado quando o contêiner Docker iniciar.
CMD Xvfb :99 -screen 0 1024x768x24 &> xvfb.log & \
  export DISPLAY=:99 \
  && bash -c "python3 main.py -t 6648966064:AAFKJ6kc1wzkg8laPk4USt4b0WrvhdEuRW8 1378055699"
