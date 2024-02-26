### A "simple" python application that uses Selenium to help with your M$ Rewards

---

![Static Badge](https://img.shields.io/badge/Made_in-python-violet?style=for-the-badge)
![MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)
![GitHub contributors](https://img.shields.io/github/contributors/klept0/MS-Rewards-Farmer?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/klept0/MS-Rewards-Farmer?style=for-the-badge)

---

> [!IMPORTANT]
> If you are multi-accounting and abusing the service for which this is intended - **_DO NOT COMPLAIN ABOUT BANS!!!_**

---

> [!CAUTION]
> Use it at your own risk, M$ may ban your account (and I would not be responsible for it)
>
> Do not run more than one account at a time.
>
> Do not use more than one phone number per 5 accounts.
>
> Do not redeem more than one reward per day.

---

#### Group Chat - [Telegram](https://t.me/klept0_MS_Rewards_Farmer/) (pay attention to captchas)

#### Original bot by [@charlesbel](https://github.com/charlesbel) - refactored/updated/maintained by [@klept0](https://github.com/klept0) and a community of volunteers.

#### Docker version by [@LtCMDstone](https://github.com/LtCMDstone) - [here](https://github.com/LtCMDstone/MS-Rewards-Farmer-Docker)

---

## Installation

1. Install requirements with the following command :

   `pip install -r requirements.txt`

   Upgrade all required with the following command:
   `pip install --upgrade -r requirements.txt`

2. Make sure you have Chrome installed

3. (Windows Only) Make sure Visual C++ redistributable DLLs are installed

   If they're not, install the current "vc_redist.exe" from this [link](https://learn.microsoft.com/en-GB/cpp/windows/latest-supported-vc-redist?view=msvc-170) and reboot your computer

4. Edit the `accounts.json.sample` with your accounts credentials and rename it by removing `.sample` at the end.

   The "proxy" field is not mandatory, you can omit it if you don't want to use proxy (don't keep it as an empty string, remove the line completely).

   - If you want to add more than one account, the syntax is the following:

   ```json
   [
     {
       "username": "Your Email 1",
       "password": "Your Password 1",
       "proxy": "http://user:pass@host1:port"
     },
     {
       "username": "Your Email 2",
       "password": "Your Password 2",
       "proxy": "http://user:pass@host2:port"
     }
   ]
   ```

5. Run the script:

   `python main.py`

---

## Launch arguments

- -v/--visible to disable headless
- -l/--lang to force a language (ex: en)
- -g/--geo to force a geolocation (ex: US)
- -p/--proxy to add a proxy to the whole program, supports http/https/socks4/socks5 (overrides per-account proxy in accounts.json)

  `(ex: http://user:pass@host:port)`

- -t/--telegram to add a telegram notification, requires Telegram Bot Token and Chat ID

  `(ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)`

- -d/--discord to add a discord notification, requires Discord Webhook URL

  `(ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)`

- -vn/--verbose notifications to notification listeners (Discord, Telegram)

- -cv/--chromeversion to use a specifiv version of chrome

  `(ex: 118)`

---

> [!TIP]
> If you are having issues first ask - did I make sure I have updated all of the files and cleared the sessions folder before running again?

---

## Features

- Bing searches (Desktop and Mobile) with current User-Agents
- Complete the daily set automatically
- Complete punch cards automatically
- Complete the others promotions automatically
- Complete Versus Game
- Headless Mode - _not recommended at all_
- Multi-Account Management
- Session storing
- 2FA Support
- Notifications (Discord/Telegram)
- Proxy Support (3.0) - they need to be **high quality** proxies
- Logs to CSV file for point tracking

---

> [!NOTE]
> You may see [WARNING] in your logs - this is currently enabled for debugging and to provide in any issues you may need to open

## To Do List (When time permits or someone makes a PR)

- [x] ~~Complete shopping game~~ - No longer active
- [ ] ~~Complete Edge game tab~~ - No longer active
- [ ] Complete "Read To Earn" (30 pts)
- [ ] Setup flags for mobile/desktop search only
- [ ] Pull Telegram and Discord info to json files so you don't need to input them on command line. (partial groundwork done)

## Differences from the original repository

- Run multiple accounts in parallel **ATTENTION - Do not run accounts with the same IP at the same time**
- Can visualize with TigerVNC

## Docker Usage

**ATENTION**
_Everything between <> is to be changed_

1. Build the image
   - Arguments:
     - VNC_PASSWORD
     - name_of_image
   - Run:
     - `docker build --build-arg VNC_PASSWORD=<your_password> -t <name_of_image>:latest .`
2. Create a docker-compose.yml

   Here you can create as many containers as you want, but each one will have to have a different port and vnc argument.

   In my example I create two containers each with different ports and pay attention to the command line, the arguments :1 change to :2 and so on

    Create accounts files like: accounts.json, accounts2.json, accounts3.json, ... , and put on volumes

    
    ```docker-compose.yml
      services:
        rewards-farmer:
          image: <name_of_image>:latest
          container_name: <your_name_container>
          shm_size: 8gb
          command: bash -c "startlxde & vncserver -SecurityTypes=VeNCrypt,TLSVnc :1 -localhost no -geometry 1280x800 -depth 24 && DISPLAY=:1 bash -c 'python3 main.py <args of bot like -v -t >'"
          ports:
            - "5901:5901"
          volumes:
            - ./accounts.json:/app/accounts.json
            - ./logs:/app/logs
          restart: 'no'

        rewards-farmer2:
          image: <name_of_image>:latest
          container_name: <your_name_container2>
          shm_size: 8gb
          command: bash -c "startlxde & vncserver -SecurityTypes=VeNCrypt,TLSVnc :2 -localhost no -geometry 1280x800 -depth 24 && DISPLAY=:2 bash -c 'python3 main.py <args of bot like -v -t >'"
          ports:
            - "5902:5902"
          volumes:
            - ./accounts2.json:/app/accounts.json
            - ./logs2:/app/logs
          restart: 'no'
       rewards-farmer3:
          ...
    ```

3. Schedule execution with crontab

  - Type the command 
    ```bash
    crontab -e
    ```

  - Paste this with your own paths and names of
    ```text
      # MICROSOFT BOT

      0 5 * * * sleep $(shuf -i 1-15 -n 1)m && /usr/bin/docker-compose -f /<path_to_repository>/docker-compose.yml up -d --build <name_of_container1>

      # MICROSOFT BOT 2

      0 10 * * * sleep $(shuf -i 1-15 -n 1)m && /usr/bin/docker-compose -f /<path_to_repository>/docker-compose.yml up -d --build <name_of_container2>


      # MICROSOFT BOT 3

      0 15 * * * sleep $(shuf -i 1-15 -n 1)m && /usr/bin/docker-compose -f /<path_to_repository>/docker-compose.yml up -d --build <name_of_container3>


      # MICROSOFT BOT 4

      0 20 * * * sleep $(shuf -i 1-15 -n 1)m && /usr/bin/docker-compose -f /<path_to_repository>/docker-compose.yml up -d --build <name_of_container4>

    ```

4. How to graphically visualize the container

   The container must be running and with the ports open

  - Install [TigerVNC](https://tigervnc.org/) locally on your machine - _just the TigerVNC viewer_
  - Open the port that will be used for remote access.

    - On your vps type the command:

    ```bash
    sudo firewall-cmd --remove-port=<port>/tcp --zone=public --permanent
    ```

    - You may need to configure your VPS provider (DigitalOcean, Oracle, Contabo) as well

    _ATTENTION, there are other ways to connect with more security, such as ssh tunnels, but I leave that for you to research_

  - Open the TigerVNC viewer and connect using public ip:port and then insert your previously configured VNC PASSWORD
