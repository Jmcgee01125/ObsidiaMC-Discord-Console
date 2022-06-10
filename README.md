# ObsidiaMC Discord Console

Cross-platform Python and Nextcord-based Minecraft console using Discord to issue commands. 

---

## Requirements

python 3.8+

nextcord (pip install nextcord)

dotenv (pip install python-dotenv)

---

## Features

Minecraft server host with Discord bot to run commands through.

Owner/operator distinction for command permissions.

Start, stop, and send any Minecraft console commands.

Automatic, user-defined restart and backup intervals.

/query command for any user to check the server status and connected players.

Live player count using Discord activity status.

No server-side modifications necessary - runs by calling the server jarfile.

---

## Setup

1) Download this repository.

    1) Do either of the following:

        1) `git clone <repository url>` in your terminal/console.

        2) Code > Download ZIP (from the GitHub page).
  
2) Open "config/obsidia.conf" with any text editor.
  
    1) Change settings based on your preferences.

        1) If you're confused about settings, such as how to use SMTWRFD 0000, open the readme in the config folder.
    
    2) Set the directory where your server is stored. This can be relative to \_\_main__.py, or absolute.

        1) You must launch the server at least once before using it with this. Otherwise, it will crash.

3) Create a file named ".env" in the directory containing \_\_main__.py.

    1) Add "DISCORD_TOKEN=<your bot's Discord token>" to the file, e.g. DISCORD_TOKEN=abcdefg

    2) Yes, you will need to make your own Discord bot account:

        1) Go to discord.com/developers and create a new application.

        2) Go to the bot tab and make it a bot, then get the token.

        3) Go to OAuth2 -> URL Generator and invite your bot with the following:

            1) "bot" and "applications.commands" scopes.

            2) "Send Messages" and "Use Slash Commands" bot permissions.

4) Add your Discord user ID to owners.txt, and any operators to operators.txt (in the config folder).

    1) See the readme in the config folder for information about how to enter this info.

5) Start the program by running \_\_main__.py.
  
    1) Quit by using Ctrl+C in the terminal that the program runs in.


---

## Screenshots

![query](https://user-images.githubusercontent.com/38796431/161887885-3316afa7-e788-46c0-bd1f-6335a5f6a49b.png)

![authorization](https://user-images.githubusercontent.com/38796431/161887939-b42b1cb1-67ca-41c2-b1e2-bde1c797e246.png)

![arbitrary commands](https://user-images.githubusercontent.com/38796431/161887954-5e2bfa99-b324-42e3-89e0-efc42095e4c5.png)

![server log](https://user-images.githubusercontent.com/38796431/161887919-c65147a8-2154-4745-afb4-67014929e94e.png)

![backup list](https://user-images.githubusercontent.com/38796431/161887949-742256f8-a419-49f2-9230-a6b83433b8cc.png)
