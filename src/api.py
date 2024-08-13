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


def update_points(_id, points, points_today):
    """
    Função para atualizar os pontos de uma conta.
    :param _id: Nome de usuário da conta a ser atualizada.
    :param points: Novos pontos da conta.
    :return: Resposta da requisição.
    """
    url = f"{base_url}update-points"
    data = {"_id": _id, "points": points, "points_today": points_today}
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


def update_status(_id, status):
    """
    Função para atualizar o status da conta
    """
    url = f"{base_url}update-status"
    data = {"_id": _id, "status": status}
    response = requests.patch(url, json=data)
    return response.json()


def get_accounts_from_mongo():
    """
    Função para pegar todas as contas do MongoDB
    """
    client = pymongo.MongoClient("mongodb://100.68.152.79:27018/")
    db = client["mstools"]
    collection = db["accounts"]
    vps = int(os.getenv("VPS", "0"))
    json_account = int(os.getenv("JSON", "0"))

    pipeline = [
        {
            "$match": {
                "vps": vps,
                "json_account": json_account,
                "status": {"$in": ["LIVE", "WAITING"]},
                "points": {"$lt": 6500},
            }
        },
        {
            "$lookup": {
                "from": "proxies",
                "localField": "proxy",
                "foreignField": "_id",
                "as": "proxy_details",
            },
        },
        {
            "$lookup": {
                "from": "emails",
                "localField": "email",
                "foreignField": "_id",
                "as": "email",
            }
        },
        {"$unwind": "$proxy_details"},
        {"$unwind": "$email"},
        {
            "$addFields": {
                "proxy": "$proxy_details.proxy",
                "username": "$email.username",
                "password": "$email.password",
            }
        },
        {
            "$project": {"proxy_details": 0, "email": 0},
        },  # Remover o campo proxy_details
    ]

    accounts = list(collection.aggregate(pipeline))
    return accounts


get_accounts_from_mongo()
