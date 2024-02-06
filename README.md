# discord-bot-pterodactyl-py
Just a discord bot that gives you the ability to control your servers (as long as your server provider provides it)

---

- It would be nice if you would give me credit when using this
- This project SHOULD work with no issues. If there's one, open an issue and I will check it out.

---

**Instructions to run inside Docker**
1. Take `docker-compose.yml` and edit path where would be your config stored.
2. Create `config.py` from example-config.py


---

**Instructions for normal use**
1. Git Pull or Download the repo to your server
2. Add your [discord bot token](https://discord.com/developers/applications) along with your **API Credentials** , your **Host's Panel Link** and **USER_IDs** to the file in **config > config.py**
3. Navigate to **Cogs > petro.py** `SERVER IDENTIFICATION` with Pterodactyl Server identifier.
4. Navigate to the console and run `pip install -U -r requirements.txt` **(ENSURE YOUR DIRECTORY IS CORRECT BEFORE RUNNING IT)**
5. Run `python3 main.py` in the console
6. Your bot should be up and running with the commands in place

---
**How to get your API Key**

![part 1 of getting api key](https://cdn.discordapp.com/attachments/933327160687599658/1111211753875968040/image.png)
![part 2 of getting api key](https://cdn.discordapp.com/attachments/933327160687599658/1111211897451188224/image.png)

---
**How to get the server identification**

![ae](https://cdn.discordapp.com/attachments/933327160687599658/1111213492557586472/image.png)

---
**How to get my User ID**

1. Navigate to your User Settings, head to **Advanced** and enable Developer Mode
2. Right click on yourself in any server or dm
3. Click **Copy User ID**
4. That's your user ID

---

ok that's all...  *sponsor me if you'd like :)*
