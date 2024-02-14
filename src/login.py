import contextlib
import logging
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        max_attempts = 5
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
                    self.utils.tryDismissAllMessages()
                    time.sleep(5)
                    attempts += 1
                    continue
        if attempts == max_attempts:
            logging.error("[LOGIN] Maximum attempts reached. Failed to load the page.")

        if not alreadyLoggedIn:
            if isLocked := self.executeLogin():
                return "Locked"

        self.utils.goHome()
        logging.info(f"[LOGIN] Logged-in ! | {self.browser.username}")
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring you are logged into Bing...")
        self.checkBingLogin()
        logging.info(f"[LOGIN] Logged-in successfully ! | {self.browser.username}")
        return points

    def executeLogin(self):
        self.utils.waitUntilVisible(By.ID, "loginHeader", 10)
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
            self.webdriver.get("https://account.microsoft.com/")

            self.utils.waitUntilVisible(
                By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 60
            )
            logging.info("[LOGIN] Acessado account.microsoft com sucesso")

        except Exception:  # pylint: disable=broad-except
            logging.warning(
                f"[ERROR] Ao acessar account.microsoft | {self.browser.username}"
            )

    def enterPassword(self, password):
        try:
            self.utils.waitUntilClickable(By.NAME, "passwd", 20)
            self.utils.waitUntilClickable(By.ID, "idSIButton9", 20)
            # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
            # If password contains special characters like " ' or \, send_keys() will not work
            password = password.replace("\\", "\\\\").replace('"', '\\"')
            self.webdriver.execute_script(
                f'document.getElementsByName("passwd")[0].value = "{password}";'
            )
            logging.info("[LOGIN] " + "Writing password...")
            self.webdriver.find_element(By.ID, "idSIButton9").click()
            time.sleep(3)
        except Exception as e:  # pylint: disable=broad-except
            logging.warning(
                f"[ERROR] on insert password of {self.browser.username}: {e}"
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
