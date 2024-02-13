import os
import random
import typing

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
