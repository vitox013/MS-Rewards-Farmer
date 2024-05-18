import argparse
import atexit
import csv
import json
import logging
import logging.handlers as handlers
import random
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import psutil

from src import Browser, DailySet, Login, MorePromotions, PunchCards, Searches, VersusGame
from src.api import create_account, get_accounts_from_mongo, update_points, update_status, verify_can_farm
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier
from src.utils import Utils

POINTS_COUNTER = 0


def main():
    cleanup_zombie_processes()
    args = argumentParser()
    notifier = Notifier(args)
    setupLogging(args.verbosenotifs, notifier)
    # Register the cleanup function to be called on script exit
    atexit.register(cleanup_chrome_processes)

    # Load previous day's points data
    previous_points_data = load_previous_points_data()

    threads = []

    loadedAccounts = get_accounts_from_mongo()

    # Processa as contas em loadedAccounts1
    for currentAccount in loadedAccounts:

        thread = threading.Thread(
            target=process_account,
            args=(currentAccount, notifier, args, previous_points_data),
        )
        threads.append(thread)
        thread.start()
        time.sleep(90)

    # Aguarda todas as threads de loadedAccounts concluírem
    for thread in threads:
        thread.join()

    # Save the current day's points data for the next day in the "logs" folder
    save_previous_points_data(previous_points_data)
    logging.info("[POINTS] Data saved for the next day.")


def adicionar_conta_se_nao_existir(conta, lista, outras_listas):
    for item in lista:
        if conta["proxy"] == item["proxy"]:
            return
    for outra_lista in outras_listas:
        for item in outra_lista:
            if conta["username"] == item["username"]:
                return
    lista.append(conta)


def log_daily_points_to_csv(date, earned_points, points_difference):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"

    # Create a new row with the date, daily points, and points difference
    date = datetime.now().strftime("%Y-%m-%d")
    new_row = {
        "Date": date,
        "Earned Points": earned_points,
        "Points Difference": points_difference,
    }

    fieldnames = ["Date", "Earned Points", "Points Difference"]
    is_new_file = not csv_filename.exists()

    with open(csv_filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if is_new_file:
            writer.writeheader()

        writer.writerow(new_row)


def setupLogging(verbose_notifs, notifier):
    ColoredFormatter.verbose_notifs = verbose_notifs
    ColoredFormatter.notifier = notifier

    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    logs_directory = Path(__file__).resolve().parent / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                logs_directory / "activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )


def cleanup_chrome_processes():
    # Use psutil to find and terminate Chrome and Chromium processes
    for process in psutil.process_iter(["pid", "name"]):
        process_info = process.as_dict(attrs=["pid", "name"])
        if process_info["name"] in ["chrome", "chromium"]:
            try:
                psutil.Process(process_info["pid"]).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass


def cleanup_zombie_processes():
    # Iterate over all processes
    for process in psutil.process_iter(["pid", "name", "status"]):
        process_info = process.as_dict(attrs=["pid", "name", "status"])

        # Check if the process is a zombie
        if process_info["status"] == psutil.STATUS_ZOMBIE:
            try:
                # Attempt to terminate the zombie process
                process.terminate()
                # Wait for the process to terminate and check if it's gone
                gone, alive = psutil.wait_procs([process], timeout=3)
                if process in gone:
                    logging.info(f"Process {process_info['pid']} ({process_info['name']}) was terminated.")
                else:
                    logging.info(f"Failed to terminate process {process_info['pid']} ({process_info['name']}).")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Ignore if the process does not exist or access is denied
                pass


def argumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MS Rewards Farmer")
    parser.add_argument("-v", "--visible", action="store_true", help="Optional: Visible browser")
    parser.add_argument("-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)")
    parser.add_argument("-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)")
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-t",
        "--telegram",
        metavar=("TOKEN", "CHAT_ID"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)",
    )
    parser.add_argument(
        "-d",
        "--discord",
        type=str,
        default=None,
        help="Optional: Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)",
    )
    parser.add_argument(
        "-vn",
        "--verbosenotifs",
        action="store_true",
        help="Optional: Send all the logs to discord/telegram",
    )
    parser.add_argument(
        "-cv",
        "--chromeversion",
        type=int,
        default=None,
        help="Optional: Set fixed Chrome version (ex. 118)",
    )
    return parser.parse_args()


def setupAccounts() -> list:
    """Sets up and validates a list of accounts loaded from 'accounts.json'."""

    def validEmail(email: str) -> bool:
        """Validate Email."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))

    accountPath = Path(__file__).resolve().parent / "accounts.json"
    if not accountPath.exists():
        accountPath.write_text(
            json.dumps([{"username": "Your Email", "password": "Your Password"}], indent=4),
            encoding="utf-8",
        )
        noAccountsNotice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(noAccountsNotice)
        exit()
    loadedAccounts = json.loads(accountPath.read_text(encoding="utf-8"))
    for account in loadedAccounts:
        if not validEmail(account["username"]):
            logging.error(f"[CREDENTIALS] Wrong Email Address: '{account['username']}'")
            exit()
    random.shuffle(loadedAccounts)
    return loadedAccounts


def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    logging.info(f'********************{ currentAccount.get("username", "") }********************')
    accountPointsCounter = 0
    remainingSearches = 0
    remainingSearchesM = 0
    startingPoints = 0

    with Browser(mobile=False, account=currentAccount, args=args) as desktopBrowser:
        accountPointsCounter = Login(desktopBrowser).login(notifier, currentAccount)
        startingPoints = accountPointsCounter
        if startingPoints in ["Locked", "Abuse", "Unusual activity", "Verify"]:
            if startingPoints == "Locked":
                message = "🚫 Account is Locked"
                status = "LOCKED"
            elif startingPoints == "Abuse":
                message = "🚫 Account BANNED"
                status = "BANNED"
            elif startingPoints == "Unusual activity":
                message = "⚠️ Unusual activity"
                status = "UNUSUAL"
            else:
                message = "❗ Account needs to be verified"
                status = "VERIFY"

            if status:
                try:
                    update_status(currentAccount.get("username", ""), status)
                except Exception as e:
                    logging.warning("Erro ao atualizar status na api: %s", e)

                notifier.send(message, currentAccount)
            logging.error("%s | %s", message, currentAccount.get("username", ""))
            return 0
        logging.info(
            "[POINTS] You have %s points on your account", desktopBrowser.utils.formatNumber(accountPointsCounter)
        )
        # PunchCards(desktopBrowser).completePunchCards()
        MorePromotions(desktopBrowser).completeMorePromotions()
        # VersusGame(desktopBrowser).completeVersusGame()
        (
            remainingSearches,
            remainingSearchesM,
        ) = desktopBrowser.utils.getRemainingSearches()

        # Introduce random pauses before and after searches
        pause_before_search = random.uniform(11.0, 15.0)  # Random pause between 11 to 15 seconds
        time.sleep(pause_before_search)

        if remainingSearches != 0:
            accountPointsCounter = Searches(desktopBrowser).bingSearches(remainingSearches)

        pause_after_search = random.uniform(11.0, 15.0)  # Random pause between 11 to 15 seconds
        time.sleep(pause_after_search)

        desktopBrowser.utils.goHome()
        goalPoints = desktopBrowser.utils.getGoalPoints()
        goalTitle = desktopBrowser.utils.getGoalTitle()
        desktopBrowser.closeBrowser()

    if remainingSearchesM != 0:
        desktopBrowser.closeBrowser()
        with Browser(mobile=True, account=currentAccount, args=args) as mobileBrowser:
            accountPointsCounter = Login(mobileBrowser).login(notifier, currentAccount)
            accountPointsCounter = Searches(mobileBrowser).bingSearches(remainingSearchesM)

            mobileBrowser.utils.goHome()
            goalPoints = mobileBrowser.utils.getGoalPoints()
            goalTitle = mobileBrowser.utils.getGoalTitle()
            mobileBrowser.closeBrowser()

    logging.info(
        f"[POINTS] You have earned {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)} points today !"
    )
    logging.info(f"[POINTS] You are now at {desktopBrowser.utils.formatNumber(accountPointsCounter)} points !")
    goalNotifier = ""
    if goalPoints > 0:
        logging.info(
            f"[POINTS] You are now at {(desktopBrowser.utils.formatNumber((accountPointsCounter / goalPoints) * 100))}% of your goal ({goalTitle}) !\n"
        )
        goalNotifier = f"🎯 Goal reached: {(desktopBrowser.utils.formatNumber((accountPointsCounter / goalPoints) * 100))}% ({goalTitle})"

    notifier.send(
        "\n".join(
            [
                f"⭐️ Points earned today: {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)}",
                f"💰 Total points: {desktopBrowser.utils.formatNumber(accountPointsCounter)}",
                goalNotifier,
            ]
        ),
        currentAccount,
    )

    return accountPointsCounter


def export_points_to_csv(points_data):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"
    with open(csv_filename, mode="a", newline="") as file:  # Use "a" mode for append
        fieldnames = ["Account", "Earned Points", "Points Difference"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Check if the file is empty, and if so, write the header row
        if file.tell() == 0:
            writer.writeheader()

        for data in points_data:
            writer.writerow(data)


# Define a function to load the previous day's points data from a file in the "logs" folder
def load_previous_points_data():
    logs_directory = Path(__file__).resolve().parent / "logs"
    try:
        with open(logs_directory / "previous_points_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Define a function to save the current day's points data for the next day in the "logs" folder
def save_previous_points_data(data):
    logs_directory = Path(__file__).resolve().parent / "logs"
    with open(logs_directory / "previous_points_data.json", "w") as file:
        json.dump(data, file, indent=4)


def process_account(currentAccount, notifier, args, previous_points_data):
    retries = 5
    while retries > 0:
        try:
            try:
                cleanup_zombie_processes()
            except Exception:
                pass
            earned_points = executeBot(currentAccount, notifier, args)
            account_name = currentAccount.get("username", "")
            previous_points = previous_points_data.get(account_name, 0)

            # Calculate the difference in points from the prior day
            points_difference = earned_points - previous_points

            # Append the daily points and points difference to CSV and Excel
            log_daily_points_to_csv(account_name, earned_points, points_difference)

            # Update the previous day's points data
            previous_points_data[account_name] = earned_points
            try:
                if earned_points:
                    update_points(
                        currentAccount.get("username", ""),
                        earned_points,
                        points_difference,
                    )
            except Exception:
                logging.warning("Erro ao atualizar na api")
                pass
            logging.info(f"[POINTS] Data for '{account_name}' appended to the file.")
            try:
                cleanup_zombie_processes()
            except Exception:
                pass
            break  # Sair do loop se a execução for bem-sucedida
        except Exception as e:
            retries -= 1
            try:
                cleanup_zombie_processes()
            except Exception:
                pass
            if retries == 0:
                notifier.send(
                    "⚠️ Error occurred after 3 attempts, please check the log",
                    currentAccount,
                )
                logging.error(
                    f"[CRITICAL] ⚠️ Error occurred after 3 attempts. Closing thread! ⚠️ | {currentAccount.get('username', '')}"
                )
            else:
                account_name2 = currentAccount.get("username", "")
                logging.warning(f"Error occurred: {e}. Retrying... | {account_name2}")
                time.sleep(10)  # Esperar um pouco antes de tentar novamente


def retry_thread(currentAccount, notifier, args, previous_points_data):
    # Adicione aqui a lógica para tentar novamente
    logging.warning(f"Trying again... | { currentAccount.get('username', '') }")
    process_account(currentAccount, notifier, args, previous_points_data)


if __name__ == "__main__":
    main()
