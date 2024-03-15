import contextlib
import logging
import random
import re
from pathlib import Path
from typing import Any

import ipapi
import requests
import seleniumwire.undetected_chromedriver as webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from src.userAgentGenerator import GenerateUserAgent
from src.utils import Utils


class Browser:
    """WebDriver wrapper class."""

    def __init__(self, mobile: bool, account, args: Any) -> None:
        # Initialize browser instance
        self.mobile = mobile
        self.browserType = "mobile" if mobile else "desktop"
        self.headless = not args.visible
        self.username = account["username"]
        self.password = account["password"]
        self.proxy = None
        if args.proxy:
            self.proxy = args.proxy
        elif account.get("proxy"):
            self.proxy = account["proxy"]
        self.localeLang, self.localeGeo = self.getCCodeLang(
            ip=self.extrair_ip(self.proxy), lang=args.lang, geo=args.geo
        )
        logging.info(f"[LANGUAGE]: {self.localeLang} | [GEO]: {self.localeGeo}")
        self.userDataDir = self.setupProfiles()
        self.browserConfig = Utils.getBrowserConfig(self.userDataDir)
        (
            self.userAgent,
            self.userAgentMetadata,
            newBrowserConfig,
        ) = GenerateUserAgent().userAgent(self.browserConfig, mobile)
        if newBrowserConfig:
            self.browserConfig = newBrowserConfig
            Utils.saveBrowserConfig(self.userDataDir, self.browserConfig)
        self.webdriver = self.browserSetup()
        self.utils = Utils(self.webdriver)

    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, *args: Any) -> None:
        # Cleanup actions when exiting the browser context
        self.closeBrowser()

    def closeBrowser(self) -> None:
        """Perform actions to close the browser cleanly."""
        # Close the web browser
        with contextlib.suppress(Exception):
            self.webdriver.quit()

    def browserSetup(
        self,
    ) -> WebDriver:
        # Configure and setup the Chrome browser
        options = webdriver.ChromeOptions()
        # options.headless = self.headless
        options.headless = False
        options.add_argument(f"--lang={self.localeLang}-{self.localeGeo}")
        options.add_experimental_option(
            "prefs",
            {
                "intl.accept_languages": f"{self.localeLang},{self.localeLang}-{self.localeGeo}"
            },
        )

        # Reduzindo argumentos desnecessários
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-notifications")
        # Monitorar e ajustar conforme necessário
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-accelerated-2d-canvas")
        options.add_argument("--no-first-run")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=PrivacySandboxSettings4")

        seleniumwireOptions: dict[str, Any] = {"verify_ssl": False}

        if self.proxy:
            # Setup proxy if provided
            seleniumwireOptions["proxy"] = {
                "http": self.proxy,
                "https": self.proxy,
                "no_proxy": "localhost,127.0.0.1",
            }
            try:
                timezone = self.get_timezone_from_ip(self.extrair_ip(self.proxy))
                if timezone:
                    options.add_argument(f"--timezone={timezone}")
            except Exception:
                pass

        driver = webdriver.Chrome(
            options=options,
            seleniumwire_options=seleniumwireOptions,
            driver_executable_path="/usr/bin/chromedriver",
            user_data_dir=self.userDataDir.as_posix(),
        )

        seleniumLogger = logging.getLogger("seleniumwire")
        seleniumLogger.setLevel(logging.ERROR)

        if self.browserConfig.get("sizes"):
            deviceHeight = self.browserConfig["sizes"]["height"]
            deviceWidth = self.browserConfig["sizes"]["width"]
        else:
            if self.mobile:
                deviceHeight = random.randint(568, 1024)
                deviceWidth = random.randint(320, min(576, int(deviceHeight * 0.7)))
            else:
                deviceWidth = random.randint(1024, 1366)
                deviceHeight = random.randint(768, 960)
            self.browserConfig["sizes"] = {
                "height": deviceHeight,
                "width": deviceWidth,
            }
            Utils.saveBrowserConfig(self.userDataDir, self.browserConfig)

        if self.mobile:
            screenHeight = deviceHeight + 146
            screenWidth = deviceWidth
        else:
            screenWidth = deviceWidth + 55
            screenHeight = deviceHeight + 151

        logging.info(f"Screen size: {screenWidth}x{screenHeight}")
        logging.info(f"Device size: {deviceWidth}x{deviceHeight}")

        if self.mobile:
            driver.execute_cdp_cmd(
                "Emulation.setTouchEmulationEnabled",
                {
                    "enabled": True,
                },
            )

        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": deviceWidth,
                "height": deviceHeight,
                "deviceScaleFactor": 0,
                "mobile": self.mobile,
                "screenWidth": screenWidth,
                "screenHeight": screenHeight,
                "positionX": 0,
                "positionY": 0,
                "viewport": {
                    "x": 0,
                    "y": 0,
                    "width": deviceWidth,
                    "height": deviceHeight,
                    "scale": 1,
                },
            },
        )

        driver.execute_cdp_cmd(
            "Emulation.setUserAgentOverride",
            {
                "userAgent": self.userAgent,
                "platform": self.userAgentMetadata["platform"],
                "userAgentMetadata": self.userAgentMetadata,
            },
        )

        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            },
        )

        return driver

    def setupProfiles(self) -> Path:
        """
        Sets up the sessions profile for the chrome browser.
        Uses the username to create a unique profile for the session.

        Returns:
            Path
        """
        currentPath = Path(__file__)
        parent = currentPath.parent.parent
        sessionsDir = parent / "sessions"

        # Concatenate username and browser type for a plain text session ID
        sessionid = f"{self.username}"

        sessionsDir = sessionsDir / sessionid
        sessionsDir.mkdir(parents=True, exist_ok=True)
        return sessionsDir

    def getCCodeLang(self, ip, lang: str, geo: str) -> tuple:
        if lang is None or geo is None:
            try:
                if ip:
                    nfo = ipapi.location(ip)
                else:
                    nfo = ipapi.location()
                if isinstance(nfo, dict):
                    if lang is None:
                        lang = nfo["languages"].split(",")[0].split("-")[0]
                    if geo is None:
                        geo = nfo["country"]
            except Exception:  # pylint: disable=broad-except
                return ("pt", "BR")
        return (lang, geo)

    def get_timezone_from_ip(self, ip):
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return data.get("timezone")

    def extrair_ip(self, url):
        # Expressão regular para encontrar o endereço IP
        padrao = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
        match = None
        try:
            match = re.search(padrao, url)
        except Exception:
            pass

        if match:
            return match.group()

        return None
