# 🥟 Dumplingboard

An open-source Starboard clone with dumplings.


## How it works

Essentially the same as the [Starboard](https://top.gg/bot/655390915325591629) bot, but with dumplings instead of stars.

If you're not familiar with it, it works like this:

- Users place dumpling `🥟` reactions under a message
- Once a message gets 3 <sup>(by default, the value can be changed)</sup> or more dumpling reactions, it gets sent to a special channel - Dumplingboard.
- Admins can set the dumplingboard channel and the amount of reactions needed to send a message to the dumplingboard.

So, like, messages "pinned" by community.


## Setup the bot

- [Invite it on your server](https://discord.com/oauth2/authorize?client_id=1270135273996423252) <sup>(24/7 uptime is not guaranteed)</sup>

_or_

- Clone the repository<br>
```sh
git clone https://github.com/moontr3/dumplingboard.git
```

- Install the required libraries
```sh
pip install -r requirements.txt
```

- Put your token in a `.env` file
```
BOT_TOKEN=<your_token>
```

- Put your ID in the admin list in [`config.py`]('https://github.com/moontr3/dumplingboard/blob/main/config.py')

- Launch the bot
```sh
python main.py
```

- To access slash commands, send `!st` command in a server with your bot and reload your Discord client.

> Don't worry if you see a panic message in the terminal.
> It shows up everytime the database file is not found.