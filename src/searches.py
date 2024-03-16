import asyncio
import json
import logging
import random
import re
import time
from datetime import date, datetime, timedelta
from typing import List, Optional

import numpy as np
import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from unidecode import unidecode  # Importe a biblioteca unidecode

from src.browser import Browser
from src.gpt import GPT


class Searches:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils
        self.gpt = GPT()

    def get_search_terms_with_gpt(self, words_count: int) -> Optional[List[str]]:
        """
        Generate a list of search terms based on current hot topics in Brazil.

        Args:
            words_count (int): Number of search terms to generate.

        Returns:
            Optional[List[str]]: A list of search terms as strings, or None if an error occurs.
        """
        today_date = datetime.now().strftime("%d/%m")
        try:
            prompt = f"""
            Gere {words_count} termos de pesquisa unicos sobre os tópicos mais populares no Brasil hoje, dia {today_date},

            Os termos de pesquisa devem ser retornados como
            um Array de strings.

            CADA TERMO DE PESQUISA DEVE SIMULAR UM USUÁRIO PESQUISANDO SOBRE O TÓPICO.

            VOCÊ DEVE APENAS RETORNAR O ARRAY DE STRINGS INICIANDO COM [ E FINALIZANDO COM ].

            Não utilize "Como fazer...".

            Aqui está um exemplo de um Array de strings:
            ["Quando é...", "Qual...", "Quem...", "Quais...", "O que é..."]
            """
            padrao = r"\[([^]]+)\]"
            array_text = None

            terms = asyncio.run(self.gpt.generate_response(prompt=prompt))

            if terms is not None:
                match = re.search(padrao, terms)
                if match:
                    array_text = "[" + match.group(1) + "]"

                if array_text is not None:
                    array_terms = json.loads(array_text)
                else:
                    array_terms = json.loads(terms)

                if isinstance(array_terms, list):
                    logging.info(
                        f"[BING] Requested {words_count} searchs and generated {len(array_terms)} with g4f!  | {self.browser.username}"
                    )
                    return array_terms
        except Exception as e:
            logging.warning(
                f"An error occurred on get searchs terms with gpt | {self.browser.username}"
            )

        return None

    def getGoogleTrends(self, wordsCount: int) -> list:
        # Function to retrieve Google Trends search terms
        searchTerms: list[str] = []
        i = 0
        while len(searchTerms) < wordsCount:
            i += 1
            # Fetching daily trends from Google Trends API
            r = requests.get(
                f'https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0][
                "trendingSearches"
            ]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, word: str) -> list:
        # Function to retrieve related terms from Bing API
        try:
            r = requests.get(
                f"https://api.bing.com/osjson.aspx?query={word}",
                headers={"User-agent": self.browser.userAgent},
            )
            return r.json()[1]
        except Exception:  # pylint: disable=broad-except
            return []

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0):
        # Function to perform Bing searches
        logging.info(
            f"[BING] Starting {self.browser.browserType.capitalize()} Edge Bing searches... | {self.browser.username}"
        )

        search_terms = self.getGoogleTrends(numberOfSearches)

        self.webdriver.get("https://bing.com")

        random.shuffle(search_terms)

        time.sleep(5)
        self.utils.tryDismissAllMessages()

        i = 0
        attempt = 0
        for word in search_terms:
            i += 1
            logging.info(f"[BING] {i}/{numberOfSearches} | {word}")
            points = self.bingSearch(word)
            if points <= pointsCounter:
                relatedTerms = self.getRelatedTerms(word)[:1]
                j = 0
                break_triggered = False  # Flag para indicar se o break foi acionado
                for term in relatedTerms:
                    j += 1
                    logging.warning(
                        f"[BING RELATED] {i}/{numberOfSearches} | {j}/1 | {term}"
                    )
                    points = self.bingSearch(term)
                    if points > pointsCounter:
                        break_triggered = True
                        break
                if not break_triggered:
                    attempt += 1
                if attempt == 2:
                    logging.warning(
                        "[BING RELATED] Possible blockage. Refreshing the page | %s",
                        {self.browser.username},
                    )
                    self.webdriver.refresh()
                    attempt = 0
            if points > 0:
                pointsCounter = points
            else:
                break
        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )
        return pointsCounter

    def bingSearch(self, word: str):
        # Function to perform a single Bing search

        while True:
            try:

                self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
                searchbar.clear()

                for char in word:
                    searchbar.send_keys(char)
                    delay = random.uniform(0.2, 1)
                    time.sleep(delay)
                searchbar.submit()
                time.sleep(self.browser.utils.randomSeconds(120, 220))
                self.browser.utils.tryDismissAllMessages()
                # Scroll down after the search (adjust the number of scrolls as needed)
                for _ in range(3):  # Scroll down 3 times
                    self.webdriver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(
                        self.browser.utils.randomSeconds(6, 13)
                    )  # Random wait between scrolls

                return self.browser.utils.getBingAccountPoints()
            except TimeoutException:
                time.sleep(self.browser.utils.randomSeconds(7, 15))
                self.webdriver.refresh()
                logging.error(
                    "[BING] "
                    + f"Timeout, continuando pra próxima search... | {self.browser.username}"
                )
                return self.browser.utils.getBingAccountPoints()

    def get_related_terms_with_gpt(self, word: str) -> Optional[List[str]]:
        try:
            prompt = f"""
            Gere 1 termos de pesquisa relacionado a um assunto.

            Assunto: '{word}'.

            O termo de pesquisa devem ser retornado como
            um Array de string.

            CADA TERMO DE PESQUISA DEVE SIMULAR UM USUÁRIO PESQUISANDO SOBRE O ASSUNTO.

            VOCÊ DEVE APENAS RETORNAR O ARRAY DE STRINGS INICIANDO COM [ E FINALIZANDO COM ].
            """
            padrao = r"\[([^]]+)\]"
            array_text = None

            terms = asyncio.run(self.gpt.generate_response(prompt=prompt))

            if terms is not None:
                match = re.search(padrao, terms)
                if match:
                    array_text = "[" + match.group(1) + "]"

                if array_text is not None:
                    array_terms = json.loads(array_text)
                else:
                    array_terms = json.loads(terms)

                if isinstance(array_terms, list):
                    return array_terms
        except Exception:
            logging.warning(
                f"An error occurred on get related terms with gpt | {self.browser.username}"
            )

        return None
