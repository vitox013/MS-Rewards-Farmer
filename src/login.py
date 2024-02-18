import contextlib
import logging
import sys
import time
import urllib.parse

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By

from src.browser import Browser

from .constants import BASE_URL


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self, notifier, account):
        logging.info("[LOGIN] " + "Logging-in...")
        max_attempts = 3
        attempts = 0
        self.webdriver.get(
            "https://rewards.bing.com/Signin/"
        )  # changed site to allow bypassing when M$ blocks access to login.live.com randomly
        alreadyLoggedIn = False
        while attempts < max_attempts:
            try:
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]', 10
                )  # Adjust timeout as needed
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.utils.waitUntilVisible(By.ID, "loginHeader", 10)
                    break
                except Exception:  # pylint: disable=broad-except
                    try:
                        self.utils.waitUntilVisible(By.ID, "i0281", 10)
                        break
                    except Exception:  # pylint: disable=broad-except
                        self.utils.tryDismissAllMessages()
                        self.webdriver.refresh()
                        time.sleep(10)
                        attempts += 1
                        continue
        if attempts == max_attempts:
            logging.error("[LOGIN] Maximum attempts reached. Failed to load the page.")

        if not alreadyLoggedIn:
            if isLocked := self.executeLogin(notifier=notifier, account=account):
                return "Locked"

        self.checkBingLogin()
        logging.info("[LOGIN] " + "Ensuring you are logged into Bing...")
        self.utils.goHome()
        time.sleep(10)
        points = self.utils.getAccountPoints()

        logging.info(f"[LOGIN] Logged-in successfully ! | {self.browser.username}")
        return points

    def executeLogin(self, notifier, account):
        logging.info("[LOGIN] " + "Entering email...")
        time.sleep(5)
        self.utils.waitUntilClickable(By.NAME, "loginfmt", 10)
        email_field = self.webdriver.find_element(By.NAME, "loginfmt")

        while True:
            email_field.send_keys(self.browser.username)
            time.sleep(1)
            if email_field.get_attribute("value") == self.browser.username:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                break

            email_field.clear()

        try:
            self.enterPassword(self.browser.password)
            time.sleep(5)
            self.utils.tryDismissAllMessages()
            time.sleep(5)
        except Exception:  # pylint: disable=broad-except
            logging.error("[ERROR] Erro ao logar")

        try:
            self.utils.waitUntilVisible(By.ID, "iProofEmail", 20)
            notifier.send("🚫 Precisa confirmar código email", account)
            logging.error(
                "[ERROR] Precisa confirmar código email... Saindo da aplicação!"
            )
            sys.exit(1)
        except:
            pass

        errors = 0
        try:
            self.webdriver.get(BASE_URL)

            self.utils.waitUntilVisible(
                By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]', 60
            )
            logging.info(f"[LOGIN] Logged in rewardsPortal: {self.browser.username} ")
        except Exception:
            logging.warning(
                f"[LOGIN] Erro ao logar no rewardsPortal após inserir senha: {self.browser.username}"
            )
            errors += 1

        try:
            self.webdriver.get("https://account.microsoft.com/")

            self.utils.waitUntilVisible(
                By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 60
            )
        except Exception:  # pylint: disable=broad-except
            logging.warning(
                f"[ERROR] Ao acessar account.microsoft | {self.browser.username}"
            )
            errors += 1

        if errors == 2:
            logging.error(
                f"[ERROR] Erro ao acessar rewards portal e account.microsoft: {self.browser.username} | restarting..."
            )
            raise Exception()

    def enterPassword(self, password):
        try:
            time.sleep(3)
            # Define o valor do campo de senha usando JavaScript
            try:
                # self.webdriver.execute_script(
                #     f'document.getElementsByName("passwd")[0].value = "{password}";'
                # )
                self.utils.waitUntilClickable(By.ID, "i0118", 10)
                pwd_field = self.webdriver.find_element(By.ID, "i0118")

                while True:
                    logging.info("[LOGIN] " + "Writing password...")
                    pwd_field.send_keys(self.browser.password)
                    time.sleep(1)
                    if pwd_field.get_attribute("value") == self.browser.password:
                        # Clica no botão de login
                        try:
                            self.webdriver.find_element(By.ID, "idSIButton9").click()
                        except Exception as e:
                            logging.warning(
                                f"[CLICK BUTTON LOGIN] Erro on click idSIButton9 login: {self.browser.username} | Error: {e}"
                            )
                        break

                    pwd_field.clear()
            except Exception as e:
                logging.warning(
                    f"[INSERT PASSWORD] Error on inserir password: {self.browser.username} | {e} "
                )

            # Espera um tempo curto após o clique para permitir que a página carregue
            time.sleep(3)

        except Exception as e:
            logging.warning(
                f"[INSERT PASSWORD] Erro desconhecido: {self.browser.username} | {e}"
            )

    def checkBingLogin(self):
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        time.sleep(5)
        self.utils.tryDismissBingCookieBanner()
        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)
