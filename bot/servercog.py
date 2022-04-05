'''
Server commands cog

Cogs
----
ServerCog
'''


from server.server_manager import ServerManager
from bot.helpers.embedhelper import EmbedField
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import threading
import nextcord
import requests
import asyncio


class ServerCog (commands.Cog):
    '''
    Server commands cog

    Parameters
    ----------
    client: `nextcord.Client`
        Client this cog is applied to
    manager: `server.server_manager.ServerManager`
        The server manager this bot should affect
    operators: `set`
        A set of `int`s (nextcord.User.id) who can run server commands

    Commands
    --------
    server()
        command(command: `str`)
        say(message: `str`)
        stop()
        start()
        backup(name: `str`)
        listbackups()
    admin()
        restore(ame: `str`)
        deletebackup(name: `str`)
        op(user: `nextcord.User`)
        deop(user: `nextcord.User`)
    query()

    Methods
    -------
    report_help() -> `list[commandhelp.CommandHelp]`
        Report command help list
    '''

    def __init__(self, client: nextcord.Client, manager: ServerManager, operators_file: str, owners_file: str, ip: str = None):
        self.client: nextcord.Client = client
        self.manager: ServerManager = manager
        self.operators_file: str = operators_file
        self.owners_file: str = owners_file
        self.ops: set[int] = set()
        self.owners: set[int] = set()
        self.ip: str = ip
        self._load_admins()

    @nextcord.slash_command(name="server", description="Server management commands")
    async def _server(self, interaction: Interaction):
        pass

    @_server.subcommand(name="command", description="Write any command to the server console")
    async def _sv_command(self, interaction: Interaction,
                          command: str = SlashOption(required=True, description="Command to run")):
        await self._write_to_console_helper(interaction, command.strip())

    @_server.subcommand(name="say", description="Say something to the server console")
    async def _sv_say(self, interaction: Interaction,
                      message: str = SlashOption(required=True, name="message", description="Message to say")):
        await self._write_to_console_helper(interaction, f"say {message.strip()}")

    async def _write_to_console_helper(self, interaction: Interaction, content: str):
        '''Should be used for commands that are operator+ restricted. Pre-trim your content.'''
        if await self._verify_operator_and_reply(interaction) or await self._verify_server_online_and_reply(interaction):
            return
        else:
            special_result = self.manager.write(content)
            if special_result != None:
                await interaction.send(special_result, ephemeral=True)
            else:
                await interaction.send(f"Command sent.")

    @_server.subcommand(name="stop", description="Shut down the server")
    async def _sv_stop(self, interaction: Interaction):
        if await self._verify_operator_and_reply(interaction) or await self._verify_server_online_and_reply(interaction):
            return
        else:
            special_result = self.manager.stop_server()
            if special_result != None:
                await interaction.send(special_result, ephemeral=True)
            else:
                await interaction.send("Server shut down.")

    @_server.subcommand(name="start", description="Start up the server")
    async def _sv_start(self, interaction: Interaction):
        if await self._verify_operator_and_reply(interaction):
            return
        elif self.manager.server_should_be_running():
            await interaction.send("Server already running.", ephemeral=True)
        else:
            await interaction.send("Starting server.")
            # start on a new thread so as not to block the bot
            threading.Thread(target=self._start_async_minecraft_server, name="MinecraftServerThread").start()

    def _start_async_minecraft_server(self):
        '''
        Start the Minecraft server client, blocks until it closes.

        Do not call this if the server is already running!
        '''
        asyncio.run(self.manager.start_server())

    @_server.subcommand(name="log", description="Read the server log")
    async def _sv_log(self, interaction: Interaction):
        # TODO - operator, give arrows to page through entries, manager.get_latest_log()
        pass

    @_server.subcommand(name="backup", description="Make a backup for the server, leave out name to use the timestamp and respect max backups.")
    async def _sv_backup(self, interaction: Interaction,
                         name: str = SlashOption(required=False, name="name", description="Name of the backup")):
        if await self._verify_operator_and_reply(interaction):
            return
        else:
            await interaction.response.defer(ephemeral=True)
            if name != None:
                name = name.strip()
            special_result = await self.manager.backup_world(name)
            if special_result != None:
                await interaction.send(special_result)
            else:
                await interaction.send("Server backed up.")
                await interaction.channel.send(f"Server backed up by {interaction.user.mention}.")

    @_server.subcommand(name="listbackups", description="Get a list of available backups")
    async def _sv_listbackups(self, interaction: Interaction):
        # TODO - operator, account for pages, translate epochs (but keep epoch as title, translate in field text not title)
        pass

    @nextcord.slash_command(name="admin", description="Server owner commands")
    async def _admin(self, interaction: Interaction):
        pass

    @_admin.subcommand(name="restore", description="Restore the world from a given backup")
    async def _ad_restore(self, interaction: Interaction,
                          name: str = SlashOption(required=True, name="name", description="Name of the backup")):
        if await self._verify_owner_and_reply(interaction):
            return
        else:
            await interaction.response.defer(ephemeral=True)
            try:
                self.manager.restore_backup(name.strip())
            except RuntimeError:
                await interaction.send("Cannot restore while server is running.")
            except FileNotFoundError:
                await interaction.send("Specified backup does not exist.")
            else:
                await interaction.send("Backup restored.")
                await interaction.channel.send(f"Backup restored by {interaction.user.mention}.")

    @_admin.subcommand(name="deletebackup", description="Delete a given backup")
    async def _ad_deletebackup(self, interaction: Interaction,
                               name: str = SlashOption(required=True, name="name", description="Name of the backup")):
        if await self._verify_owner_and_reply(interaction):
            return
        else:
            await interaction.response.defer(ephemeral=True)
            try:
                self.manager.delete_backup(name.strip())
            except FileNotFoundError:
                await interaction.send("Specified backup does not exist.")
            else:
                await interaction.send("Backup deleted.")

    @_admin.subcommand(name="op", description="Give a user operator status")
    async def _ad_op(self, interaction: Interaction,
                     user: nextcord.User = SlashOption(required=True, name="user", description="User to op")):
        if await self._verify_owner_and_reply(interaction):
            return
        elif user.id in self.ops:
            await interaction.send("User is already an operator.", ephemeral=True)
        else:
            self.ops.add(user.id)
            self._save_admins()
            await interaction.send(f"Added {user.mention} to operator pool.")

    @_admin.subcommand(name="deop", description="Remove a user's operator status")
    async def _ad_deop(self, interaction: Interaction,
                       user: nextcord.User = SlashOption(required=True, name="user", description="User to deop")):
        if await self._verify_owner_and_reply(interaction):
            return
        elif user.id in self.owners:
            await interaction.send(f"You cannot remove operator status from an owner.", ephemeral=True)
        else:
            try:
                self.ops.remove(user.id)
            except KeyError:
                await interaction.send(f"User is not an operator.", ephemeral=True)
            else:
                self._save_admins()
                await interaction.send(f"Removed {user.mention} from operator pool.")

    @nextcord.slash_command(name="query", description="Query the server's state")
    async def _query(self, interaction: Interaction):
        # TODO - general use, make a request to mcapi and parse it. If it fails, just say if server is started, stopped, or changing state
        # TODO: if ip is None, then use_mcapi is false and we should instead just give the started/stopped/changing status
        pass

    async def _verify_operator_and_reply(self, interaction: Interaction):
        '''Return true if the user is NOT allowed to run operator commands, replying to the interaction if so.'''
        if interaction.user.id not in self.ops:
            await interaction.send(f"You are not authorized to do that.", ephemeral=True)
            return True
        return False

    async def _verify_owner_and_reply(self, interaction: Interaction):
        '''Return true if the user is NOT allowed to run owner commands, replying to the interaction if so.'''
        if interaction.user.id not in self.owners:
            await interaction.send(f"You are not authorized to do that.", ephemeral=True)
            return True
        return False

    async def _verify_server_online_and_reply(self, interaction: Interaction):
        '''Return true if the server is NOT able to run commands, replying to the interaction if so.'''
        if self.manager.server_active():
            return False
        elif self.manager.server_should_be_running():
            await interaction.send(f"The server is changing state, please wait a moment.", ephemeral=True)
            return True
        else:
            await interaction.send(f"The server is offline.", ephemeral=True)
            return True

    def _load_admins(self):
        ops_reader = open(self.operators_file, "r")
        for id in ops_reader:
            self.ops.add(int(id))

        owners_reader = open(self.owners_file, "r")
        for id in owners_reader:
            self.ops.add(int(id))
            self.owners.add(int(id))

    def _save_admins(self):
        ops_text = ""
        for operator in self.ops:
            ops_text += f"{operator}\n"
        with open(self.operators_file, "w") as ops_writer:
            ops_writer.write(ops_text)

        owners_text = ""
        for owner in self.owners:
            owners_text += f"{owner}\n"
        with open(self.owners_file, "w") as owners_writer:
            owners_writer.write(owners_text)
