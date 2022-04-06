# ObsidiaMC Web Console

Python and Nextcord-based Minecraft console using Discord to issue commands. 

---

## Requirements

python 3.9+

nextcord (pip install nextcord)

---

## Features

Minecraft server host with Discord bot to run commands through.

Owner/operator distinction for command permissions.

Start, stop, and send any Minecraft console commands.

Automatic, user-defined restarts and backups.

---

## Setup

1) Download this repository.

    1) Do either of the following:

        1) `git clone <repository url>` in your terminal/console.

        2) Code > Download ZIP (from the GitHub page).
  
2) Open "config/obsidia.conf" with any text editor.
  
    1) Change settings based on your preferences.

        1) If you're confused about settings, such as how to use SMTWRFD 0000, open the readme in the config folder.
  
        2) You can set defaults by changing settings in "config/obsidia_defaults.conf".

            1) Honestly this isn't really that relevant, it was just functionality left over from the web console version.

        3) Note that these config files are overwritten and filled in with defaults (for missing items only) when launched. Comments will be removed.
    
    2) Set the directory where your server is stored. This can be relative to \_\_main__.py, or absolute.

        1) You must launch the server at least once before using it with this. Otherwise, it will crash.

3) Create a file named ".env" in the directory containing \_\_main__.py.

    1) Add "DISCORD_TOKEN=<your bot's Discord token>" to the file, e.g. DISCORD_TOKEN=abcdefg
  
4) Start the program by running \_\_main__.py.
  
    1) Quit by using Ctrl+C in the terminal that the program runs in.


---

## Screenshots


