----- [Server Information] -----


server_jar
The name of the server jar, such as server.jar (a vanilla jar).
Some versions, like fabric, may use alternates.

world_folders
A list of world folders to back up, comma separated.
For example, both of the following are valid:
    world_folders=world
    world_folders=world, world_nether, world_the_end
These worlds should be in the same directory as server.jar, and are subject to backup/restore operations.

args
Server startup arguments, like setting the amount of RAM.
These arguments are parsed as "java <args> -jar <jarname> -nogui"


----- [Restarts] -----


autorestart
Automatically restart the server at specific times.

autorestart_datetime
The datetime to restart the server at (No effect if autorestart is false).
Follows the format of SMTWRFD HHMM, where SMTWRFD indicates days (Sun -> Sat) when a restart should occur.
HHMM is the time, in 24 hour time (0000 -> 2359) that the restart should happen at.
Players are given a 15 minute, 5 minute, and 1 minute warning before restarts.

restart_on_crash
Automatically restart the server when it goes down.
You MUST send a stop command via Discord to fully shut down a server.
(Stop commands sent in-game will be interpreted as crashes).


----- [Backups] -----


backup
If true, do backups at the specified interval.

max_backups
The maximum number of backups to keep.
Older backups will be deleted when new ones are made.
To disable, use a value less than or equal to 0.

backup_datetime
The datetime to backup the server at (No effect if backup is false).
Follows the format of SMTWRFD HHMM, where SMTWRFD indicates days (Sun -> Sat) when a backup should occur.
HHMM is the time, in 24 hour time (0000 -> 2359) that the backup should happen at.

backup_folder
The folder to make backups in.
This folder is nested within the server's directory.


----- [Server] -----


directory
The directory where the server is located.
This is the directory that contains server.jar.
Directories from root/C/whatever are recommended, but not required (relative to the location of __main__.py).

ip
The ip that users will connect to.
This is only used in the information displayed in the Discord activity ("Playing 192.168.1.1") and queries ("192.168.1.1:25565").
As such, you can technically make it whatever you want. Note that the port is always appended (e.g. "MyServer:25565").
If left blank, the name will instead simply be "Minecraft" with no other information.


----- [operators.txt] -----


A list of Discord account IDs (one per line) that have operator status.
You can get this by enabling developer mode on Discord and doing right click -> Copy ID on the account name name.
This file is also updated using the /server op and /server deop commands (as owner).


----- [owners.txt] -----


A list of Discord account IDs (one per line) that have owner status.
You can get this by enabling developer mode on Discord and doing right click -> Copy ID on the account name.
This file can only be updated manually, and represents the highest form of ownership.
Owners are automatically added to the list of operators, so it is not necessary to op yourself as an owner.
