import json

import requests

# Base URL
base_url = "http://172.21.0.2:3143/accounts/"


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
