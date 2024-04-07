#!/bin/bash

# Gera um número aleatório entre 1 e 15 e espera esse número de minutos
sleep $(shuf -i 1-15 -n 1)m

# Verifica se há containers com o nome "ms-reward-farmer" em execução
container_ids=$(/usr/bin/docker ps -qf "name=ms-reward-farmer")

# Se houver algum container com o nome "ms-reward-farmer" em execução, para ele
if [ -n "$container_ids" ]; then
    echo "Parando container(s) com o nome 'ms-reward-farmer'..."
    # Itera sobre cada ID de container e para o container correspondente
    for container_id in $container_ids; do
        /usr/bin/docker stop $container_id
    done
else
    echo "Nenhum container com o nome 'ms-reward-farmer' encontrado em execução."
fi

# O argumento $1 é o nome do serviço do Docker Compose
service_name=$1

# Verifica se o argumento foi passado
if [ -z "$service_name" ]; then
    echo "Por favor, especifique o nome do serviço do Docker Compose."
    exit 1
fi

# Executa o comando docker-compose para o serviço especificado
/usr/bin/docker-compose -f /home/ubuntu/Documents/GitHub/MS-Rewards-Farmer/docker-compose.yml up -d --build $service_name
