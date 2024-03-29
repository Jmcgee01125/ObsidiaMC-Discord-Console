'''
Server commands cog

Cogs
----
ServerCog
'''


from bot.buttonviews import ButtonEnums, ConfirmButtons, PageButtons
from nextcord import Interaction, SlashOption, Embed
from server.server_manager import ServerManager
from bot.helpers.embedhelper import EmbedField
from typing import Callable, Union, Dict, List
import bot.helpers.embedhelper as embedhelper
from server.server_ping import StatusPing
from nextcord.ext import commands
from datetime import datetime
import threading
import nextcord
import asyncio
import os


class ServerCog (commands.Cog):
    '''
    Server commands cog

    Parameters
    ----------
    client: `nextcord.Client`
        Client this cog is applied to
    manager: `server.server_manager.ServerManager`
        The server manager this bot should affect
    operators_file: `str`
        The file to read operators from
    owners_file: `str`
        The file to read owners from, owners are given operator status
    manager_logfile: `str`
        The file to read when calling /server managerlog
    pinger: `StatusPing`
        The object to use when pinging the server
    server_name: `str`
        The server name as it appears in queries
    server_ip: `str`
        The server IP as it should appear in query descriptions (e.g. "192.168.1.1:25565"), None to ignore

    Commands
    --------
    server()
        command(command: `str`)
        say(message: `str`)
        stop()
        start()
        log()
        managerlog()
        backup(name: `str`)
        listbackups()
    admin()
        restore(name: `str`)
        deletebackup(name: `str`)
        op(user: `nextcord.User`)
        deop(user: `nextcord.User`)
    query()
    '''

    def __init__(self, client: nextcord.Client, manager: ServerManager, operators_file: str, owners_file: str,
                 manager_logfile: str, pinger: StatusPing, server_name: Union[str, None] = "Minecraft Server", server_ip: Union[str, None] = None):
        self.client: nextcord.Client = client
        self.manager: ServerManager = manager
        self.operators_file: str = operators_file
        self.owners_file: str = owners_file
        self.manager_logfile: str = manager_logfile
        self.pinger = pinger
        self._ops: set[int] = set()
        self._owners: set[int] = set()
        self._server_name = server_name
        self._server_ip = server_ip
        self._embed_color = nextcord.Color.green()
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
        special_result = self.manager.write(content)
        if special_result != None:
            await interaction.send(special_result, ephemeral=True)
        else:
            await interaction.send(f"Command sent.", ephemeral=True)

    @_server.subcommand(name="stop", description="Shut down the server")
    async def _sv_stop(self, interaction: Interaction):
        if await self._verify_operator_and_reply(interaction) or await self._verify_server_online_and_reply(interaction):
            return
        await interaction.send("Shutting down server.")
        self.manager.stop_server()

    @_server.subcommand(name="start", description="Start up the server")
    async def _sv_start(self, interaction: Interaction):
        if await self._verify_operator_and_reply(interaction):
            return
        elif self.manager.server_should_be_running():
            await interaction.send("Server already running.", ephemeral=True)
            return
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
        if await self._verify_operator_and_reply(interaction):
            return
        embed_title = "Server Log"
        log_entries = self.manager.get_latest_log()
        await self._start_log_view(interaction, log_entries, embed_title)

    @_server.subcommand(name="managerlog", description="Read the manager log")
    async def _sv_managerlog(self, interaction: Interaction):
        if await self._verify_operator_and_reply(interaction):
            return
        embed_title = "Manager Log"
        try:
            log_entries = open(self.manager_logfile, "r").readlines()
        except IOError:
            log_entries = ["No manager log found."]
        await self._start_log_view(interaction, log_entries, embed_title)

    @_server.subcommand(name="backup", description="Make a backup for the server, leave out name to use the timestamp and respect max backups.")
    async def _sv_backup(self, interaction: Interaction,
                         name: str = SlashOption(required=False, name="name", description="Name of the backup")):
        if await self._verify_operator_and_reply(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        if name != None:
            name = name.strip()
        special_result = await self.manager.backup_world(name)
        if special_result != None:
            await interaction.send(special_result)
        else:
            await interaction.send("Server backed up.")
            if interaction.user != None and type(interaction.channel) == nextcord.channel.TextChannel:
                await interaction.channel.send(f"Server backed up by {interaction.user.mention}.")  # type: ignore

    @_server.subcommand(name="listbackups", description="Get a list of available backups")
    async def _sv_listbackups(self, interaction: Interaction):
        if await self._verify_operator_and_reply(interaction):
            return
        embed_title = "Available Backups"
        backup_list = sorted(self.manager.list_backups())
        if len(backup_list) >= 10:  # max 10 fields per discord embed, so offer buttons to page through them
            def build_backup_embed_with_offset(backups: List[str], title: str, index: int) -> Embed:
                fields = []
                for i in range(index, min(index + 10, len(backups))):
                    fields.append(self._build_backup_field(backups[i]))
                return embedhelper.build_embed(*fields, title=title, color=self._embed_color)
            await self._manage_pageable_embed(interaction, backup_list, embed_title, build_backup_embed_with_offset)
        else:  # less than 10, no need for buttons
            fields = []
            for backup in backup_list:
                fields.append(self._build_backup_field(backup))
            emb = embedhelper.build_embed(*fields, title=embed_title, color=self._embed_color)
            await interaction.send(embed=emb, ephemeral=True)

    def _build_backup_field(self, backup: str) -> EmbedField:
        try:  # try to translate epochs, otherwise read the file creation date
            backup_timestamp = datetime.fromtimestamp(int(backup)).strftime("%D %H:%M:%S")
        except ValueError:
            try:
                st = os.path.getmtime(os.path.join(self.manager.backup_directory, backup))
                backup_timestamp = datetime.fromtimestamp(int(st)).strftime("%D %H:%M:%S")
            except FileNotFoundError:
                backup_timestamp = "Could not get timestamp"
        return EmbedField(backup, backup_timestamp)

    @nextcord.slash_command(name="admin", description="Server owner commands")
    async def _admin(self, interaction: Interaction):
        pass

    @_admin.subcommand(name="restore", description="Restore the world from a given backup")
    async def _ad_restore(self, interaction: Interaction,
                          name: str = SlashOption(required=True, name="name", description="Name of the backup")):
        if await self._verify_owner_and_reply(interaction):
            return
        name = name.strip()
        button_timeout = 15
        buttons = ConfirmButtons(timeout=button_timeout)
        await interaction.send(f"Are you sure you want to restore {name}?", view=buttons, ephemeral=True)
        while not buttons.is_finished():
            await buttons.wait()
            if buttons.user == interaction.user:  # ephemeral anyway, but can't hurt
                if buttons.value == ButtonEnums.DENY:
                    await interaction.edit_original_message(content="Canceled restoration.", view=None)
                elif buttons.value == ButtonEnums.ACCEPT:
                    try:
                        await interaction.edit_original_message(content="Working...", view=None)
                        await self.manager.restore_backup(name)
                    except RuntimeError:
                        await interaction.edit_original_message(content="Cannot restore while server is running.", view=None)
                    except FileNotFoundError:
                        await interaction.edit_original_message(content="Specified backup does not exist.", view=None)
                    else:
                        await interaction.edit_original_message(content=f"Backup {name} restored.", view=None)
                        if interaction.user != None and type(interaction.channel) == nextcord.channel.TextChannel:
                            await interaction.channel.send(f"Backup {name} restored by {interaction.user.mention}.")  # type: ignore
            elif buttons.user != None:
                buttons = ConfirmButtons(timeout=button_timeout)
                await interaction.edit_original_message(view=buttons)
        if buttons.value == None:
            await interaction.edit_original_message(content="Request timed out.", view=None)

    @_admin.subcommand(name="deletebackup", description="Delete a given backup")
    async def _ad_deletebackup(self, interaction: Interaction,
                               name: str = SlashOption(required=True, name="name", description="Name of the backup")):
        if await self._verify_owner_and_reply(interaction):
            return
        name = name.strip()
        button_timeout = 15
        buttons = ConfirmButtons(timeout=button_timeout)
        await interaction.send(f"Are you sure you want to delete {name}?", view=buttons, ephemeral=True)
        while not buttons.is_finished():
            await buttons.wait()
            if buttons.user == interaction.user:  # ephemeral anyway, but can't hurt
                if buttons.value == ButtonEnums.DENY:
                    await interaction.edit_original_message(content="Canceled deletion.", view=None)
                elif buttons.value == ButtonEnums.ACCEPT:
                    try:
                        await interaction.edit_original_message(content="Working...", view=None)
                        self.manager.delete_backup(name.strip())
                    except FileNotFoundError:
                        await interaction.edit_original_message(content="Specified backup does not exist.", view=None)
                    else:
                        await interaction.edit_original_message(content=f"Backup {name} deleted.", view=None)
            elif buttons.user != None:
                buttons = ConfirmButtons(timeout=button_timeout)
                await interaction.edit_original_message(view=buttons)
        if buttons.value == None:
            await interaction.edit_original_message(content="Request timed out.", view=None)

    @_admin.subcommand(name="op", description="Give a user operator status")
    async def _ad_op(self, interaction: Interaction,
                     user: nextcord.User = SlashOption(required=True, name="user", description="User to op")):
        if await self._verify_owner_and_reply(interaction):
            return
        elif user.id in self._ops:
            await interaction.send("User is already an operator.", ephemeral=True)
            return
        self._ops.add(user.id)
        self._save_admins()
        await interaction.send(f"Added {user.mention} to operator pool.")

    @_admin.subcommand(name="deop", description="Remove a user's operator status")
    async def _ad_deop(self, interaction: Interaction,
                       user: nextcord.User = SlashOption(required=True, name="user", description="User to deop")):
        if await self._verify_owner_and_reply(interaction):
            return
        elif user.id in self._owners:
            await interaction.send(f"You cannot remove operator status from an owner.", ephemeral=True)
            return
        try:
            self._ops.remove(user.id)
        except KeyError:
            await interaction.send(f"User is not an operator.", ephemeral=True)
        else:
            self._save_admins()
            await interaction.send(f"Removed {user.mention} from operator pool.")

    @nextcord.slash_command(name="query", description="Query the server's state")
    async def _query(self, interaction: Interaction,
                     hidden: bool = SlashOption(default=True, required=False, name="hidden", description="Make false to let everyone see this query")):
        if await self._verify_server_online_and_reply(interaction):
            return
        response = self.pinger.get_status()
        if response == None:
            await interaction.send("Request timed out.", ephemeral=True)
            return
        version = self._read_dict_with_default(response, *["version", "name"], default_value="Unknown")
        players_max = self._read_dict_with_default(response, *["players", "max"], default_value="?")
        players_online = self._read_dict_with_default(response, *["players", "online"], default_value="?")
        players_text = ""
        try:
            players_list = response["players"]["sample"]
            for player in players_list:
                players_text += f"{player['name']}, "
            players_text = players_text[:-2]
        except KeyError:
            pass
        motd = self._read_dict_with_default(response, *["description", "text"], default_value="\n")
        if self._server_ip != None:
            motd = f"{self._server_ip}\n\n{motd}"
        elif motd == None or motd == "":  # otherwise would crash embed, and not guaranteed default
            motd = "\n"
        fields = []
        fields.append(EmbedField("Online", players_online, inline=True))
        fields.append(EmbedField("Capacity", players_max, inline=True))
        fields.append(EmbedField("Version", version, inline=True))
        if players_text != "":
            fields.append(EmbedField("Current Players", players_text, inline=False))
        emb = embedhelper.build_embed(*fields, title=self._server_name, description=motd, color=self._embed_color)
        await interaction.send(embed=emb, ephemeral=hidden)

    def _read_dict_with_default(self, dict: Dict[str, str], *keys: str, default_value: Union[str, None] = None) -> str:
        try:
            # HACK this is a really stupid way of iterating a dict
            value = dict
            for key in keys:
                value = value[key]  # type: ignore
            return value  # type: ignore
        except KeyError:
            if default_value == None:
                raise RuntimeError("Could not find key in dict and no default value provided.")
            else:
                return default_value

    async def _start_log_view(self, interaction: Interaction, log_entries: List[str], embed_title: str):
        def build_log_embed_with_offset(logs: List[str], title: str, index: int) -> Embed:
            content = ""
            for i in range(max(0, index), min(index + 10, len(logs))):
                content += f"{logs[i]}\n"
            return embedhelper.build_embed(title=title, description=content, color=self._embed_color)
        await self._manage_pageable_embed(interaction, log_entries, embed_title, build_log_embed_with_offset, start_index=len(log_entries) - 10)

    async def _manage_pageable_embed(self,
                                     interaction: Interaction,
                                     items: List,
                                     embed_title: str,
                                     embed_builder: Callable[[List, str, int], Embed],
                                     start_index: int = 0):
        index = start_index
        button_timeout = 30
        page_buttons = PageButtons(timeout=button_timeout)
        try:
            await interaction.send(embed=embed_builder(items, embed_title, index), view=page_buttons, ephemeral=True)
        except:
            await interaction.send(content="Error getting page.", view=page_buttons, ephemeral=True)
        while not page_buttons.is_finished():
            await page_buttons.wait()
            if page_buttons.value == ButtonEnums.LEFT:
                if index > 0:
                    index -= 10
                page_buttons = PageButtons(timeout=button_timeout)
                try:
                    await interaction.edit_original_message(content="", embed=embed_builder(items, embed_title, index), view=page_buttons)
                except:
                    await interaction.edit_original_message(content="Error getting page.", embed=None, view=page_buttons)
            elif page_buttons.value == ButtonEnums.RIGHT:
                if index < len(items) - 10:
                    index += 10
                page_buttons = PageButtons(timeout=button_timeout)
                try:
                    await interaction.edit_original_message(content="", embed=embed_builder(items, embed_title, index), view=page_buttons)
                except:
                    await interaction.edit_original_message(content="Error getting page.", embed=None, view=page_buttons)
        await interaction.edit_original_message(view=None)

    async def _verify_operator_and_reply(self, interaction: Interaction):
        '''Return true if the user is NOT allowed to run operator commands, replying to the interaction if so.'''
        if interaction.user != None and interaction.user.id not in self._ops:
            await interaction.send(f"You are not authorized to do that.", ephemeral=True)
            return True
        return False

    async def _verify_owner_and_reply(self, interaction: Interaction):
        '''Return true if the user is NOT allowed to run owner commands, replying to the interaction if so.'''
        if interaction.user != None and interaction.user.id not in self._owners:
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
            self._ops.add(int(id))

        owners_reader = open(self.owners_file, "r")
        for id in owners_reader:
            self._ops.add(int(id))
            self._owners.add(int(id))

    def _save_admins(self):
        ops_text = ""
        for operator in self._ops:
            ops_text += f"{operator}\n"
        with open(self.operators_file, "w") as ops_writer:
            ops_writer.write(ops_text)

        owners_text = ""
        for owner in self._owners:
            owners_text += f"{owner}\n"
        with open(self.owners_file, "w") as owners_writer:
            owners_writer.write(owners_text)
