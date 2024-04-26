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

    def login(self, notifier, account):
        logging.info("[LOGIN] " + f"Logging-in... | {self.browser.username}")
        self.webdriver.get(
            "https://rewards.bing.com/Signin/"
        )  # changed site to allow bypassing when M$ blocks access to login.live.com randomly
        alreadyLoggedIn = False
        attempt = 0
        while True:
            try:
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]', 14
                )
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.utils.focus_on_login()
                    self.utils.waitUntilVisible(
                        By.XPATH,
                        '//*[@id="i0116"] | //*[@id="loginHeader"] | //*[@id="usernameTitle"] | //input[@name="loginfmt"] | //input[@id="i0118"] | //input[@name="passwd"]',
                        60,
                    )
                    break
                except Exception:  # pylint: disable=broad-except
                    attempt += 1
                    if attempt == 3:
                        logging.warning(
                            "[LOGIN] Error on find loginHeader e loginHeader... Raising exception | %s",
                            self.browser.username,
                        )
                        raise Exception()
                    if self.utils.tryDismissAllMessages():
                        continue

        if not alreadyLoggedIn:
            status = self.executeLogin()
            if status is not None:
                if status == "Error_login":
                    raise Exception()
                return status

        self.utils.tryDismissCookieBanner()
        logging.info("[LOGIN] " + f"Logged-in ! | {self.browser.username}")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring you are logged into Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully ! | %s", self.browser.username)
        return points

    def executeLogin(self):
        logging.info("[LOGIN] " + "Entering email...")

        try:
            self.utils.focus_on_login()
            self.utils.waitUntilClickable(By.NAME, "loginfmt", 10)
            email_field = self.webdriver.find_element(By.NAME, "loginfmt")

            while True:
                email_field.send_keys(self.browser.username)
                time.sleep(3)
                if email_field.get_attribute("value") == self.browser.username:
                    self.webdriver.find_element(By.ID, "idSIButton9").click()
                    break

                email_field.clear()
                time.sleep(3)
        except Exception:  # pylint: disable=broad-except
            pass

        try:
            self.enterPassword()
        except Exception as e:  # pylint: disable=broad-except
            logging.error(
                f"[ERROR] Erro na etapa de inserir password: {self.browser.username} | Error: {e}"
            )
            return "Error_login"
        self.utils.focus_on_login()
        self.utils.tryDismissAllMessages()
        if self.verify_abuse():
            return "Abuse"
        if self.verify_unusual_activity():
            return "Unusual activity"

        try:
            self.utils.waitUntilVisible(By.XPATH, '//*[@id="authenticatorIntro"]')
            self.webdriver.find_element(By.XPATH, '//*[@id="iCancel"]').click()
        except Exception:
            pass

        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/"
            and urllib.parse.urlparse(self.webdriver.current_url).hostname
            == "account.microsoft.com"
        ):
            if (
                urllib.parse.urlparse(self.webdriver.current_url).hostname
                == "rewards.bing.com"
            ):
                self.webdriver.get("https://account.microsoft.com")

            if "Abuse" in str(self.webdriver.current_url):
                logging.error(f"[LOGIN] {self.browser.username} is locked")
                return "Locked"
            self.utils.tryDismissAllMessages()
            time.sleep(1)

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10
        )

    def enterPassword(self):
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work

        logging.info("[LOGIN] " + "Writing password...")
        # self.webdriver.find_element(By.ID, "idSIButton9").click()
        time.sleep(3)
        attempt = 0
        while True:
            if attempt == 5:
                raise Exception()
            pwd_field = self.get_pwd_field()
            if pwd_field:
                try:
                    pwd_field.clear()
                except Exception:
                    pass
                if self.insert_pwd(pwd_field):
                    time.sleep(5)
                    if not self.click_next():
                        attempt += 1
                        continue
                    if self.had_error_on_insert_pwd():
                        logging.warning(
                            "[LOGIN] Tentando inserir senha novamente... | %s",
                            self.browser.username,
                        )
                        attempt += 1
                        continue
                    break
                attempt += 1
            else:
                attempt += 1
                time.sleep(10)

    def click_next(self):
        with contextlib.suppress(Exception):
            self.utils.waitUntilClickable(By.ID, "idSIButton9")
        try:
            button = self.webdriver.find_element(By.ID, "idSIButton9")
            button.click()
            logging.info("[Login] I clicked log in | %s", self.browser.username)
            return True
        except Exception:
            try:
                button = self.webdriver.find_element(By.ID, "idSIButton9")
                self.webdriver.execute_script("arguments[0].click();", button)
                logging.info("[Login] I clicked log in | %s", self.browser.username)
                return True
            except Exception as e:
                logging.warning(
                    f"[Error] On click next button: {self.browser.username} | {e}"
                )
                return False

    def get_pwd_field(self):
        try:
            self.utils.focus_on_login()
            self.utils.waitUntilClickable(
                By.XPATH, '//input[@id="i0118"] | //input[@name="passwd"]'
            )
            pwd_field = self.webdriver.find_element(
                By.XPATH, '//input[@id="i0118"] | //input[@name="passwd"]'
            )
            return pwd_field
        except Exception:
            # Melhorando a lógica de busca com document.evaluate
            script = """
            var xpath = '//input[@id="i0118"] | //input[@name="passwd"]';
            var result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            return result.singleNodeValue;
            """
            try:
                pwd_field = self.webdriver.execute_script(script)
                if pwd_field:
                    return pwd_field

                return None
            except Exception:
                logging.warning(
                    "[LOGIN] Password field not found... Trying again | %s",
                    self.browser.username,
                )
                return None

    def insert_pwd(self, pwd_field):
        try:
            pwd_field.send_keys(self.browser.password)
            return True
        except Exception:
            try:
                self.webdriver.execute_script(
                    f'document.getElementsByName("passwd")[0].value = "{self.browser.password}";'
                )
                return True
            except Exception as e:
                return False

    def had_error_on_insert_pwd(self):
        try:
            self.utils.waitUntilVisible(By.XPATH, '//*[@id="passwordError"]', 5)
            return True
        except Exception:
            try:
                self.utils.waitUntilVisible(By.XPATH, "//div[@role='alert']", 5)
                return True
            except Exception:
                return False

    def checkBingLogin(self):
        try:
            self.webdriver.get(
                "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
            )
        except Exception:
            logging.error(
                f"[ERROR BING] Erro ao verificar login pelo bing... Retrying | {self.browser.username}"
            )
            raise Exception()

        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)

    def verify_abuse(self):
        try:
            self.utils.waitUntilVisible(
                By.XPATH,
                '//div[contains(@class, "serviceAbusePageContainer")] | //*[@id="suspendedAccountHeader"]',
                timeToWait=5,
            )
            return True
        except Exception:
            pass

    def verify_unusual_activity(self):
        try:
            self.utils.waitUntilVisible(
                By.XPATH,
                '//*[@id="identityPageBanner"]',
                timeToWait=10,
            )
            return True
        except Exception:
            pass
