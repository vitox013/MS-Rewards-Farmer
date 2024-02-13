import asyncio
import json
import os
import random
import re
import typing
from typing import List, Optional

import g4f
import requests


class GPT:
    def __init__(self):
        self.proxies = []

    async def generate_response(self, prompt: str) -> typing.Optional[str]:
        """Generates a response to the given prompt from g4f."""
        self.proxies = self.get_proxies()
        for proxy in self.proxies:
            try:
                response = await g4f.ChatCompletion.create_async(
                    model=g4f.models.gpt_4_turbo,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    proxy=f"http://{proxy}",
                    timeout=20,
                )  # type: ignore
                return response
            except Exception as e:  # pylint: disable=broad-except
                print(e)
                continue
        return None

    def get_proxies(self):
        """Return a list of proxies"""
        proxy_url = os.getenv("PROXY_URL")
        response = requests.get(proxy_url, timeout=30)  # type: ignore
        proxies = response.text.split("\r\n")
        proxies = self.reformat_proxies(proxies)
        random.shuffle(proxies)
        return proxies

    def test_proxy_with_site(self, proxy):
        """Test proxys"""
        proxies = {"http": f"http://{proxy}"}

        try:
            response = requests.get("http://www.bing.com", proxies=proxies, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as err:
            print(f"Proxy falhou: {err}")
            return False

    def reformat_proxies(self, proxies):
        """Formata para ficar no formato ideal"""
        reformatted_proxies = []
        for proxy in proxies:
            if proxy == "":
                continue
            host, port, username, password = proxy.split(":")
            reformatted_proxy = f"{username}:{password}@{host}:{port}"
            reformatted_proxies.append(reformatted_proxy)
        return reformatted_proxies

    def get_search_terms_from_gpt(self, words_count: int) -> Optional[List[str]]:
        """
        Generate a list of search terms based on current hot topics in Brazil.

        Args:
            words_count (int): Number of search terms to generate.

        Returns:
            Optional[List[str]]: A list of search terms as strings, or None if an error occurs.
        """
        try:
            prompt = f"""
            Gere {words_count} termos de pesquisa sobre os tópicos mais populares no Brasil hoje,

            Os termos de pesquisa devem ser retornados como
            um Array de strings.

            CADA TERMO DE PESQUISA DEVE SIMULAR UM USUÁRIO PESQUISANDO SOBRE O TÓPICO.

            VOCÊ DEVE APENAS RETORNAR O ARRAY DE STRINGS INICIANDO COM [ E FINALIZANDO COM ].

            Aqui está um exemplo de um Array de strings:
            ["Como...", "Quando é...", "Qual..."]
            """
            padrao = r"\[([^]]+)\]"
            array_text = None

            terms = asyncio.run(self.generate_response(prompt=prompt))

            if terms is not None:
                match = re.search(padrao, terms)
                if match:
                    array_text = "[" + match.group(1) + "]"

                if array_text is not None:
                    array_terms = json.loads(array_text)
                else:
                    array_terms = json.loads(terms)

                if isinstance(array_terms, list):
                    print(
                        f"[BING] Requested {words_count} searchs and generated {len(array_terms)} with g4f!"
                    )
                    return array_terms
        except Exception as e:
            print(f"An error occurred on get search from gpt: {e}")

        return None
