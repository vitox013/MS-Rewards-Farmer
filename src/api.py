import json
import os

import pymongo
import requests

# Base URL
base_url = "http://100.68.152.79:3143/accounts/"


def create_account(username, points):
    """
    Função para criar uma conta.
    :param username: Nome de usuário da conta a ser criada.
    :param points: Pontos iniciais da conta.
    :return: Resposta da requisição.
    """
    url = f"{base_url}create"
    data = {"username": username, "points": points}
    response = requests.post(url, json=data)
    return response.json()


def update_points(username, points, points_today):
    """
    Função para atualizar os pontos de uma conta.
    :param username: Nome de usuário da conta a ser atualizada.
    :param points: Novos pontos da conta.
    :return: Resposta da requisição.
    """
    url = f"{base_url}update-points"
    data = {"username": username, "points": points, "points_today": points_today}
    response = requests.post(url, json=data)
    return response.json()


def verify_can_farm(username):
    """
    Função para saber se a conta pode farmar ou não
    """
    url = f"{base_url}get-canfarm"
    params = {"username": username}
    response = requests.get(url, params=params)
    return response.status_code


def update_status(username, status):
    """
    Função para atualizar o status da conta
    """
    url = f"{base_url}update-status"
    data = {"username": username, "status": status}
    response = requests.patch(url, json=data)
    return response.json()


def get_accounts_from_mongo():
    """
    Função para pegar todas as contas do MongoDB
    """
    client = pymongo.MongoClient("mongodb://100.68.152.79:27018/")
    db = client["test"]
    collection = db["accounts"]
    vps = int(os.getenv("VPS", "0"))
    json_account = int(os.getenv("JSON", "0"))

    pipeline = [
        {"$match": {"vps": vps, "json_account": json_account, "status": "LIVE", "points": {"$lt": 6500}}},
        {"$lookup": {"from": "proxies", "localField": "proxy", "foreignField": "_id", "as": "proxy_details"}},
        {"$unwind": "$proxy_details"},  # Descompactar o array de proxy_details
        {"$addFields": {"proxy": "$proxy_details.proxy"}},  # Substituir o campo proxy
        {"$project": {"proxy_details": 0}},  # Remover o campo proxy_details
    ]

    return list(collection.aggregate(pipeline))
