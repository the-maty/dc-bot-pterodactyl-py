from logging import error
import asyncio
import subprocess
import requests
import discord
from discord.ext import commands, tasks
from pydactyl import PterodactylClient
import humanfriendly
from humanfriendly import format_size, format_timespan
from config.config import pterodactylapikey, pterodactyldomain, AUTHORIZED_USERS
from discord.commands import slash_command, option

# NOTES:
# ServerIdentification SHOULD be the Name of the Server you will be identifying it as
# server id SHOULD be the ID of the server.

api = PterodactylClient(pterodactyldomain, pterodactylapikey)
SERVER_ID_LIST = ["Enshrouded"]

def is_authorized():
    def predicate(ctx):
        #print(f"Checking authorization for user {ctx.author.id}...")
        result = ctx.author.id in AUTHORIZED_USERS
        #print(f"Authorization check result: {result}")
        return result

    return commands.check(predicate)

async def authchecker(ctx: discord.AutocompleteContext):
    """
    Returns a list of the Server Identification from the SERVER_ID_LIST list.
    In this example, we've added logic to only display any results in the
    returned list if the user's ID exists in the BASIC_ALLOWED list.
    This is to demonstrate passing a callback in the discord.utils.basic_autocomplete function.
    """

    return [id for id in SERVER_ID_LIST if ctx.interaction.user.id in AUTHORIZED_USERS]

class ServerError:
    """There was a server error during a power action"""
    pass

class ptrodactylcontrols(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_presence.start()

   # THE SERVER IDENTIFICATION MUST BE SAME AS THE ONE PROVIDED ABOVE. SPACES ARE NOT ALLOWED DUE TO HOW IT WORKS
    def Convert_Friendly_Name_to_ID(self, server_id):
        """A common function to use to convert custom identifiers to server IDs"""
        if server_id == "Enshrouded":
            server_id = "6cb65669"
        return server_id

    @tasks.loop(minutes=1)
    async def update_presence(self):
        global global_error_type
        server_id = "6cb65669"  # Replace with the actual server ID now only works when one ID in future more
        response = None  # Initialize response variable

        try:
            # Check if the host is available before fetching server information
            subprocess.run(["ping", "-c", "1", "-q", "-W", "1", "192.168.2.241"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            response = api.client.servers.get_server_utilization(server_id, detail=True)

            if response["attributes"]["current_state"] == "running":
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="tvou rodinu"))
            else:
                await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name="tvou rodinu"))

        except asyncio.TimeoutError:
            print("Timeout error detected")
            global_error_type = "timeout"
        except subprocess.CalledProcessError as e:
            #print(f"Error when host down: {e}")
            global_error_type = "host_unreachable"
            # Set bot presence to idle when the host is unreachable
            await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name="host status ❌"))

        except Exception as e:
            print(f"Error updating presence: {e}")
            global_error_type = "other"

    @update_presence.before_loop
    async def before_update_presence(self):
        await self.bot.wait_until_ready()

    @slash_command(description="Pterodactyl control commands")
    @option(name="server",autocomplete=discord.utils.basic_autocomplete(authchecker))
    @option(name="action", choices=["on", "start", "off", "stop","restart", "status", "sendcommand", "kill"])
    @option(name="command", description="The command to run on the server", required=False)
    async def server(self, ctx: commands.Context, server: str, action: str, command:str):
        """
        Power commands for servers.
        """
        server_id = self.Convert_Friendly_Name_to_ID(server)

        # Authorization check
        if not await is_authorized().predicate(ctx):
            return await ctx.respond("❌ You are not authorized to use this command.", ephemeral=True)
        
        if action.lower() == "on" or action.lower() == "start":
            try:
                api.client.servers.send_power_action(server_id, "start")
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"✅ Starting the server - `{server} [{server_id}]`"
                        )
                    )
            except:
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"❌ Something went wrong while starting - `{server} [{server_id}]`"
                        )
                    )
        elif action.lower() == "off" or action.lower() == "stop":
            try:
                api.client.servers.send_power_action(server_id, "stop")
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"✅ Stopping the server - `{server} [{server_id}]`"
                    )
                )
            except:
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"❌ Something went wrong while stopping the server - `{server}`".format(command)
                        )
                    )
        elif action.lower() == "restart":
            try:
                api.client.servers.send_power_action(server_id, "restart")
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"✅ Restarting the server - `{server} [{server_id}]`"
                        )
                    )
            except:
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"❌ Something went wrong while restarting the server - `{server} [{server_id}]`".format(command)
                        )
                    )
        elif action.lower() == "sendcommand":
            if command == None:
                return await ctx.respond(
                    embed=discord.Embed(
                        description="❌ Hey buddy, you need to specify a command to send",
                        color=0xB51818,
                    )
                )
            try:
                response = api.client.servers.send_console_command(server_id, command)
                if response.status_code == 204:
                    await ctx.respond(
                        embed=discord.Embed(
                            description=f"✅ Sent command `{command}` to the server - `{server} [{server_id}]`"
                        )
                    )
                else:
                    pass
            except requests.exceptions.HTTPError:
                await ctx.respond(
                    embed=discord.Embed(
                        description="❌ There was a server error while processing that console command, please try again later",
                        color=0xB51818,
                    )
                )
                raise ServerError  # type: ignore
        elif action.lower() == "status":
            try:
                response = api.client.servers.get_server_utilization(server_id, detail=True)
                if response["attributes"]["is_suspended"] == "True":
                    await ctx.respond(embed=discord.Embed(description="❗ The server is suspended, please contact the server provider to resolve this issue"))
                
                elif response["attributes"]["current_state"] == "running":
                    e = response["attributes"]["resources"]["uptime"] / 1000.0
                    h = humanfriendly.format_timespan(e)
                    memory = humanfriendly.format_size(
                        response["attributes"]["resources"]["memory_bytes"]
                    )
                    disk = humanfriendly.format_size(
                        response["attributes"]["resources"]["disk_bytes"]
                    )
                    upload = humanfriendly.format_size(
                        response["attributes"]["resources"]["network_rx_bytes"]
                    )
                    download = humanfriendly.format_size(
                        response["attributes"]["resources"]["network_tx_bytes"]
                    )
                    ramlimit = "unlimited"
                    disklimit = "unlimited"
                    # YOU WILL HAVE TO MANUALLY ADD THE LIMIT PROVIDED BY YOUR SERVER PROVIDER DUE TO PTERODACTYL LIMITATION(s).
                    # YOU MAY REMOVE THE DISK/RAM LIMIT(s) DOWN BELOW IF THERE IS NO LIMIT ON YOUR PTERODACTYL SERVER.
                    if server_id == "6cb65669":
                        ramlimit = "4 GiB"
                    embed = discord.Embed(
                        title="Server Details",
                        description=f"""
                    **• Status:** `💚 Running`
                    **• SERVER ID:** `{server_id}`
                    ==============================================
                    __**SERVER UTILIZATION**__
                    **• Memory:** `{memory}/{ramlimit}`
                    **• CPU:** `{response['attributes']['resources']['cpu_absolute']}%`
                    **• Disk:** `{disk}/{disklimit}`
                    ==============================================
                    __**SERVER NETWORK UTILIZATION**__
                    **• Inbound:** `{download}`
                    **• Outbound:** `{upload}`
                    ==============================================
                    __**SERVER UPTIME**__
                    **• Uptime:** `{h}`
                    """,
                        color=0x57F287,
                    )
                    await ctx.respond(embed=embed)
                elif response["attributes"]["current_state"] == "offline":
                    embed = discord.Embed(
                        title="Server Details",
                        description=f"""
                    **• Status:** `💔 Offline`
                    **• SERVER ID:** `{server_id}`
                    ==============================================
                    __**SERVER UTILIZATION**__
                    **• Memory:** `OFFLINE`
                    **• CPU:** `OFFLINE`
                    **• Disk:** `OFFLINE`
                    ==============================================
                    __**SERVER NETWORK UTILIZATION**__
                    **• Inbound:** `OFFLINE`
                    **• Outbound:** `OFFLINE`
                    ==============================================
                    __**SERVER UPTIME**__
                    **• Uptime:** `OFFLINE`
                    """,
                        color=0xED4245,
                    )
                    await ctx.respond(embed=embed)
                else:
                    await ctx.respond(embed=discord.Embed(description="❗ The server is either in the middle of a power action, or its not responding"))
            except requests.exceptions.HTTPError:
                await ctx.respond(embed=discord.Embed(description="❗ There was an error while looking up the server status, please try again later",color=0xB51818))
        elif action.lower() == "kill":
            try:
                api.client.servers.send_power_action(server_id, "kill")
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"✅ Killing the server - `{server} [{server_id}]`"
                        )
                    )
            except:
                await ctx.respond(
                        embed=discord.Embed(
                            description=f"❌ Something went wrong while killing the server - `{server} [{server_id}]`"
                        )
                    )
        else:
            await ctx.respond(
                        embed=discord.Embed(
                            description=f"❌ **Invalid action**, please use `start`, `stop`, `restart`, `sendcommand`, `kill` or `status`"
                        )
                    )   
    

    @commands.command()
    @commands.is_owner()
    async def start(self, ctx, server_id=None):
        if server_id == None:
            await ctx.send(
                embed=discord.Embed(
                    description="Hey buddy, you need to specify a server identifier or server id",
                    color=0xB51818,
                )
            )
            return
        else:
            # Use a common function cross commands to convert
            server_id = self.Convert_Friendly_Name_to_ID(server_id)
        try:
            response = api.client.servers.send_power_action(server_id, "start")
            if response.status_code == 204:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"Starting the server {ctx.author.mention}, please wait while it starts!",
                        color=0x842899,
                    )
                )
            else:
                pass
        except requests.exceptions.HTTPError:
            await ctx.send(
                embed=discord.Embed(
                    description="There was a server error while processing that power action, please try again later",
                    color=0xB51818,
                )
            )
            raise ServerError  # type: ignore

    @commands.command()
    @commands.is_owner()
    async def stop(self, ctx, server_id=None):
        if server_id == None:
            await ctx.send(
                embed=discord.Embed(
                    description="Hey buddy, you need to specify a server identifier or server id",
                    color=0xB51818,
                )
            )
            return
        else:
            # Use a common function cross commands to convert
            server_id = self.Convert_Friendly_Name_to_ID(server_id)
        try:
            response = api.client.servers.send_power_action(server_id, "stop")
            if response.status_code == 204:
                await ctx.send(
                    embed=discord.Embed(
                        description="Stopping the server, hope you had a great time!"
                    )
                )
            else:
                pass
        except requests.exceptions.HTTPError:
            await ctx.send(
                embed=discord.Embed(
                    description="There was a server error while processing that power action, please try again later",
                    color=0xB51818,
                )
            )
            raise ServerError  # type: ignore

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx, server_id=None):
        if server_id == None:
            await ctx.send(
                embed=discord.Embed(
                    description="Hey buddy, you need to specify a server identifier or server id",
                    color=0xB51818,
                )
            )
            return
        else:
            # Use a common function cross commands to convert
            server_id = self.Convert_Friendly_Name_to_ID(server_id)
        try:
            response = api.client.servers.send_power_action(server_id, "restart")
            if response.status_code == 204:
                await ctx.send(
                    embed=discord.Embed(
                        description="Restarting the server, give it a minute!"
                    )
                )
            else:
                pass
        except requests.exceptions.HTTPError:
            await ctx.send(
                embed=discord.Embed(
                    description="There was a server error while processing that power action, please try again later",
                    color=0xB51818,
                )
            )
            raise ServerError  # type: ignore

    @commands.command()
    @commands.is_owner()
    async def sendcommand(self, ctx, server_id=None, *, cmd=None):
        if server_id == None:
            await ctx.send(
                embed=discord.Embed(
                    description="Hey buddy, you need to specify a server identifier or server id",
                    color=0xB51818,
                )
            )
            return
        else:
            # Use a common function cross commands to convert
            server_id = self.Convert_Friendly_Name_to_ID(server_id)
        if cmd == None:
            return await ctx.send(
                embed=discord.Embed(
                    description="Hey buddy, you need to specify a command to send",
                    color=0xB51818,
                )
            )
        try:
            response = api.client.servers.send_console_command(server_id, cmd)
            if response.status_code == 204:
                await ctx.send(
                    embed=discord.Embed(
                        description="Sent command `{}` to the server".format(cmd)
                    )
                )
            else:
                pass
        except requests.exceptions.HTTPError:
            await ctx.send(
                embed=discord.Embed(
                    description="There was a server error while processing that console command, please try again later",
                    color=0xB51818,
                )
            )
            raise ServerError  # type: ignore

    @commands.command()
    @commands.is_owner()
    async def status(self, ctx, server_id=None):
        if server_id == None:
            await ctx.send(
                embed=discord.Embed(
                    description="Hey buddy, you need to specify a server identifier or server id",
                    color=0xB51818,
                )
            )
            return
        try:
            # Use a common function cross commands to convert
            server_id = self.Convert_Friendly_Name_to_ID(server_id)
        except:
            pass
        try:
            response = api.client.servers.get_server_utilization(server_id, detail=True)
            if response["attributes"]["is_suspended"] == "True":
                await ctx.send(
                    embed=discord.Embed(
                        description="The server is suspended, please contact the server provider to resolve this issue"
                    )
                )
            elif response["attributes"]["current_state"] == "running":
                e = response["attributes"]["resources"]["uptime"] / 1000.0
                h = humanfriendly.format_timespan(e)
                memory = humanfriendly.format_size(
                    response["attributes"]["resources"]["memory_bytes"]
                )
                disk = humanfriendly.format_size(
                    response["attributes"]["resources"]["disk_bytes"]
                )
                upload = humanfriendly.format_size(
                    response["attributes"]["resources"]["network_rx_bytes"]
                )
                download = humanfriendly.format_size(
                    response["attributes"]["resources"]["network_tx_bytes"]
                )
                ramlimit = "unlimited"
                disklimit = "unlimited"
                # YOU WILL HAVE TO MANUALLY ADD THE LIMIT PROVIDED BY YOUR SERVER PROVIDER DUE TO PTERODACTYL LIMITATION(s).
                # YOU MAY REMOVE THE DISK/RAM LIMIT(s) DOWN BELOW IF THERE IS NO LIMIT ON YOUR PTERODACTYL SERVER.
                if server_id == "6cb65669":
                    ramlimit = "4 GiB"
                embed = discord.Embed(
                    title="Server Details",
                    description=f"""
                **• Status:** `💚 Running`
                **• SERVER ID:** `{server_id}`
                ==============================================
                __**SERVER UTILIZATION**__
                **• Memory:** `{memory}/{ramlimit}`
                **• CPU:** `{response['attributes']['resources']['cpu_absolute']}%`
                **• Disk:** `{disk}/{disklimit}`
                ==============================================
                __**SERVER NETWORK UTILIZATION**__
                **• Inbound:** `{download}`
                **• Outbound:** `{upload}`
                ==============================================
                __**SERVER UPTIME**__
                **• Uptime:** `{h}`
                """,
                    color=0x57F287,
                )
                await ctx.send(embed=embed)
            elif response["attributes"]["current_state"] == "offline":
                embed = discord.Embed(
                    title="Server Details",
                    description=f"""
                **• Status:** `💔 Offline`
                **• SERVER ID:** `{server_id}`
                ==============================================
                __**SERVER UTILIZATION**__
                **• Memory:** `OFFLINE`
                **• CPU:** `OFFLINE`
                **• Disk:** `OFFLINE`
                ==============================================
                __**SERVER NETWORK UTILIZATION**__
                **• Inbound:** `OFFLINE`
                **• Outbound:** `OFFLINE`
                ==============================================
                __**SERVER UPTIME**__
                **• Uptime:** `OFFLINE`
                """,
                    color=0xED4245,
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        description="The server is either in the middle of a power action, or its not responding"
                    )
                )
        except requests.exceptions.HTTPError:
            await ctx.send(
                embed=discord.Embed(
                    description="There was an error while looking up the server status, please try again later",
                    color=0xB51818,
                )
            )
            raise ServerError  # type: ignore
        
    @slash_command(description="Check bot latency")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        """
        Check bot latency.
        """

        # Authorization check
        if not await is_authorized().predicate(ctx):
            return await ctx.respond("❌ You are not authorized to use this command.", ephemeral=True)

        try:
            # Defer the initial response
            await ctx.defer()

            result = subprocess.run(['ping', '-c', '4', 'google.com'], stdout=subprocess.PIPE, text=True, check=True)

            # Extract the round-trip time from the output
            ping_time = float(result.stdout.split('time=')[-1].split(' ')[0])

            # Edit the message with the reply
            await ctx.edit(
                embed=discord.Embed(
                    description=f"🏓 Pong! Latency: {ping_time}ms"
                )
            )
        except subprocess.CalledProcessError as e:
            await ctx.respond(f"❌ Error: {e}", ephemeral=True)
        except commands.CommandOnCooldown as e:
            # Correctly handle the cooldown error
            await ctx.respond(f"❌ Command is on cooldown. Please try again in {e.retry_after:.2f} seconds.", ephemeral=True)

def setup(bot):
    bot.add_cog(ptrodactylcontrols(bot))