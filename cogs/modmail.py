import asyncio
import datetime
import os
import random
from contextlib import closing

import discord
import mariadb
from discord import Embed
from discord import File
from discord.ext import commands

import db
from settings import enso_embedmod_colours, blank_space


# Method to ask the user if they want to be anonymous or not
def AnonOrNot(author):
    # Set up embed to let the user how to start sending modmail
    AnonModMailEmbed = Embed(title="**Want to send it Anonymously?**",
                             colour=enso_embedmod_colours,
                             timestamp=datetime.datetime.utcnow())

    AnonModMailEmbed.set_thumbnail(url=author.avatar_url)
    AnonModMailEmbed.set_footer(text=f"Sent by {author}")

    fields = [(blank_space, "**We understand that for some things,"
                            "you may want to remain Anonymous."
                            "\nUse the reactions below to choose!**", False),
              (blank_space, "**Use :white_check_mark: for** `Yes`", True),
              (blank_space, "**Use :x: for** `No`", True),
              (blank_space, blank_space, True),
              (blank_space,
               "The Staff will not know who is sending this"
               "\nPurely negative feedback will not be considered.", True)]

    for name, value, inline in fields:
        AnonModMailEmbed.add_field(name=name, value=value, inline=inline)

    return AnonModMailEmbed


# Method to send an embed to to let the user know to type into chat
def SendInstructions(author):
    # Set up embed to let the user know that they have aborted the modmail
    SendModMailEmbed = Embed(title="**Please enter a message for it to be sent to the staff!**",
                             colour=enso_embedmod_colours,
                             timestamp=datetime.datetime.utcnow())

    SendModMailEmbed.set_thumbnail(url=author.avatar_url)
    SendModMailEmbed.set_footer(text=f"Sent by {author}")

    fields = [("**Make sure that the message is above **50** and below **1024** characters!**",
               "**Include as much detail as possible :P**",
               False)]

    for name, value, inline in fields:
        SendModMailEmbed.add_field(name=name, value=value, inline=inline)

    return SendModMailEmbed


# Method to let the user know that the message must be above 50 characters
def ErrorHandling(author):
    # Set up embed to let the user know that the message must be above 50 characters
    ErrorHandlingEmbed = Embed(
        title="Uh Oh! Please make sure the message is above **50** and below **1024** characters!",
        colour=enso_embedmod_colours,
        timestamp=datetime.datetime.utcnow())

    ErrorHandlingEmbed.set_thumbnail(url=author.avatar_url)
    ErrorHandlingEmbed.set_footer(text=f"Sent by {author}")

    fields = [("Please enter in a message which is above **50** and below **1024** characters!",
               "**This helps us reduce spam and allows you to include more detail in your mail!**",
               False)]

    for name, value, inline in fields:
        ErrorHandlingEmbed.add_field(name=name, value=value, inline=inline)

    return ErrorHandlingEmbed


# Method to send an embed into chat to let the user know that their mail has been sent successfully
def MessageSentConfirmation(author):
    # Set up embed to let the user know that they have sent the mail
    ConfirmationEmbed = Embed(title="**Message relayed to Staff!!**",
                              colour=enso_embedmod_colours,
                              timestamp=datetime.datetime.utcnow())

    ConfirmationEmbed.set_thumbnail(url=author.avatar_url)
    ConfirmationEmbed.set_footer(text=f"Sent by {author}")

    fields = [("Thank you for your input! The staff team appreciate it very much!",
               f"\n As mentioned previously, please don't be hesistant to DM the Staff for anything! :P",
               False)]

    for name, value, inline in fields:
        ConfirmationEmbed.add_field(name=name, value=value, inline=inline)

    return ConfirmationEmbed


# Method to actually allow the message to be sent to #mod-mail
def SendMsgToModMail(self, msg, author):
    if self.anon:

        avatars = ["https://cdn.discordapp.com/embed/avatars/0.png",
                   "https://cdn.discordapp.com/embed/avatars/1.png",
                   "https://cdn.discordapp.com/embed/avatars/2.png",
                   "https://cdn.discordapp.com/embed/avatars/3.png",
                   "https://cdn.discordapp.com/embed/avatars/4.png"]

        embed = Embed(title="Modmail",
                      colour=enso_embedmod_colours,
                      timestamp=datetime.datetime.utcnow())

        embed.set_thumbnail(url=random.choice(avatars))
        embed.set_footer(text=f"Sent By Anon Member")

        fields = [("Member", "Anon Member", False),
                  ("Message", msg.content, False)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        return embed

    else:
        embed = Embed(title="Modmail",
                      colour=enso_embedmod_colours,
                      timestamp=datetime.datetime.utcnow())

        embed.set_thumbnail(url=author.avatar_url)
        embed.set_footer(text=f"Sent By {author}")

        fields = [("Member", author, False),
                  ("Message", msg.content, False)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        return embed


# Set up the Cog
class Modmail(commands.Cog):
    """Set up modmail system!"""

    def __init__(self, bot):
        self.bot = bot
        self.anon = None

    @commands.group(invoke_without_command=True, hidden=True)
    async def modmail(self, ctx):
        pass

    @modmail.command()
    async def setup(self, ctx, channelID: int):
        """Setup modmail system"""

        # Retrieve a list of channel id's in the guild
        channels = [channel.id for channel in ctx.guild.channels]

        # Checking if the guild already exists within the database
        with db.connection() as conn:
            # Get the author's row from the Members Table
            select_query = """SELECT * FROM moderatormail WHERE guildID = (?)"""
            val = ctx.author.guild.id,
            with closing(conn.cursor()) as cursor:
                # Execute the SQL Query
                cursor.execute(select_query, val)
                result = cursor.fetchone()

            # Throw error if the guild already exists and then stop the function
            if result is not None:
                await ctx.send("**Looks like this guild already has a modmail system set up!" +
                               f"\nPlease check `{ctx.prefix}help` for information on how to update/delete existing information**")
                return

        # As long as the channel exists within the guild
        if channelID in channels:

            # Ask for the channel ID that the modmail should be logged to
            await ctx.send("**Please enter the ID of the channel you want your modmail to be sent**")

            # Check the response is from the author and from the same channel as the previous message
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            # Wait for the message from the author
            msg = await self.bot.wait_for('message', check=check)

            # As long as the channel exists within the guild
            if int(msg.content) in channels:

                # Set up embed to let the user how to start sending modmail
                ModMail = Embed(title="**Welcome to Modmail!**",
                                colour=enso_embedmod_colours,
                                timestamp=datetime.datetime.utcnow())

                ModMail.set_thumbnail(url=self.bot.user.avatar_url)

                # Define fields to be inserted into the embed
                fields = [
                    ("React to this message if you want to send a message to the Staff Team!",
                     "**React with ✅**", False),
                    ("We encourage all suggestions/thoughts and opinions on the server!" +
                     "\nAs long as it is **valid** criticism.",
                     "**Purely negative feedback will not be considered**", False)]

                # Add the fields to the embed
                for name, value, inline in fields:
                    ModMail.add_field(name=name, value=value, inline=inline)

                try:
                    # Get the channel object from the channelID input by the user
                    channel = ctx.author.guild.get_channel(channelID)
                    modmailchannelID = await channel.send(embed=ModMail)
                    # Auto add the ✅ reaction
                    await modmailchannelID.add_reaction('✅')

                    # Store the information within the database
                    with db.connection() as conn:
                        # Define the insert statement that will insert information about the modmail channel
                        insert_query = """INSERT INTO moderatormail (guildID, channelID, messageID, modmailChannelID) VALUES (?, ?, ?, ?)"""
                        vals = ctx.author.guild.id, channelID, modmailchannelID.id, int(msg.content),
                        with closing(conn.cursor()) as cursor:
                            # Execute the SQL Query
                            cursor.execute(insert_query, vals)

                    await ctx.send("**Your Modmail system is now successfully set up!" +
                                   f"\nPlease refer to `{ctx.prefix}help` for any information**")
                    return

                except mariadb.IntegrityError as err:
                    print(err)
                    await ctx.send("Looks like this guild already has a modmail system set up!" +
                                   f"\nPlease check `{ctx.prefix}help` for information on how to update/delete existing information")
            else:
                # Send error message if the channel ID is not recognised
                await ctx.send("**Invalid Channel ID. Aborting Process...**")
                return
        else:
            # Send error message if the channel ID is not recognised
            await ctx.send("**Invalid Channel ID. Aborting Process...**")
            return

    @modmail.command()
    async def update(self, ctx, channelID: int):
        """Update modmail system"""

        # Retrieve a list of channel id's in the guild
        channels = [channel.id for channel in ctx.guild.channels]

        # Checking if the guild already exists within the database
        with db.connection() as conn:
            # Get the author's row from the Members Table
            select_query = """SELECT * FROM moderatormail WHERE guildID = (?)"""
            vals = ctx.author.guild.id,
            with closing(conn.cursor()) as cursor:
                # Execute the SQL Query
                cursor.execute(select_query, vals)
                result = cursor.fetchone()

        # Throw error if the guild already exists and then stop the function
        if result is None:
            await ctx.send("**Looks like this guild does not have a modmail system setup!" +
                           f"\nPlease check `{ctx.prefix}help` for information on how to update/delete existing information**")
            return

        # As long as the channel exists within the guild
        if channelID in channels:

            try:
                # Store the information within the database
                with db.connection() as conn:
                    # Define the insert statement that will insert information about the modmail channel
                    update_query = """UPDATE moderatormail SET modmailChannelID = (?) WHERE guildID = (?)"""
                    vals = channelID, ctx.author.guild.id
                    with closing(conn.cursor()) as cursor:
                        # Execute the SQL Query
                        cursor.execute(update_query, vals)
                        conn.commit()

            except mariadb.Error as err:
                print(err)
                await ctx.send("**Looks like something went wrong during the update!"
                               "\nMake sure that the Channel ID is correct!**")

            channel = ctx.author.guild.get_channel(channelID)
            await ctx.send(
                f"**The channel has been updated! Your new modmail will be sent to** {channel.mention}")

        else:
            # Send error message if the channel ID is not recognised
            await ctx.send("**Invalid Channel ID. Aborting Process...**")
            return

    @modmail.command()
    async def delete(self, ctx):
        """Delete modmail system"""

        # Checking if the guild already exists within the database
        with db.connection() as conn:
            # Get the author's row from the Members Table
            select_query = """SELECT * FROM moderatormail WHERE guildID = (?)"""
            vals = ctx.author.guild.id,
            with closing(conn.cursor()) as cursor:
                # Execute the SQL Query
                cursor.execute(select_query, vals)
                result = cursor.fetchone()

            # Throw error if the guild already exists and then stop the function
            if result is None:
                await ctx.send("**Looks like this guild does not have a modmail system setup!" +
                               f"\nPlease check `{ctx.prefix}help` for information on how to update/delete existing information**")
                return

        try:
            # Store the information within the database
            with db.connection() as conn:
                # Define the delete statement to remove all information about the guild
                delete_query = """DELETE FROM moderatormail WHERE guildID = (?)"""
                vals = ctx.author.guild.id,
                with closing(conn.cursor()) as cursor:
                    # Execute the SQL Query
                    cursor.execute(delete_query, vals)
                    conn.commit()

        except mariadb.Error as err:
            print(err)
            await ctx.send("**Looks like this guild has not set up the modmail system yet!" +
                           f"\nPlease do `{ctx.prefix}help` to find out how to set it up!**")

        # Sending confirmation message that the modmail system has been deleted
        await ctx.send("**Modmail system successfully deleted!" +
                       f"\nPlease do `{ctx.prefix}help` to find out how to set Modmail again!**")

    # Setting up Listener to listen for reactions within the modmail channel created
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Don't count reactions that are made by the bot
        if payload.user_id == self.bot.user.id:
            return
        # Don't count other reactions other than ✅ and ❌
        elif payload.user_id:
            if str(payload.emoji) not in ['✅', '❌']:
                return

        # Find a role corresponding to the Emoji name.
        guildid = payload.guild_id

        # Use database connection
        with db.connection() as conn:

            # Get the author's row from the Members Table
            select_query = """SELECT * FROM moderatormail WHERE guildID = (?)"""
            val = guildid,
            with closing(conn.cursor()) as cursor:
                # Execute the SQL Query
                cursor.execute(select_query, val)
                result = cursor.fetchone()

                # Adding error handlingpip3 install
                if result is None:
                    return

                # Define variables
                guild_id = int(result[0])
                channel_id = int(result[1])
                message_id = int(result[2])
                modmail_channel_id = int(result[3])

        # Bunch of checks to make sure it has the right guild, channel, message and reaction
        if payload.guild_id == guild_id and payload.channel_id == channel_id and payload.message_id == message_id and payload.emoji.name == "✅":

            # Get the guild
            guild = self.bot.get_guild(payload.guild_id)
            # Get the member
            member = guild.get_member(payload.user_id)
            # Get the setup modmail channel
            channel = guild.get_channel(payload.channel_id)
            # Get the modmail logging channel
            modmail_channel = guild.get_channel(modmail_channel_id)

            # Fetch the message and remove the reaction
            reaction = await channel.fetch_message(message_id)
            await reaction.remove_reaction('✅', member)

            # Setting up the channel permissions for the new channel that will be created
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Saving this for later within when discord.py 1.4 comes out
            # cat = await guild.create_category_channel(member.name, overwrites=overwrites)

            # Create the text channel
            user_channel = await guild.create_text_channel(member.name, overwrites=overwrites,
                                                           position=0)

            # Mention the user to make sure that they get pinged
            mention = await user_channel.send(member.mention)
            await mention.delete()

            try:

                # Send the embed if they want to remain anonymous or not
                Anon_or_Not = await user_channel.send(embed=AnonOrNot(member))
                # Add reactions to the message
                await Anon_or_Not.add_reaction('✅')
                await Anon_or_Not.add_reaction('❌')

                # Checking if the user reacted with ✅ with response to sending staff a message
                def emoji_check(reaction, user):
                    return user == member and str(reaction.emoji) in ['✅', '❌']

                # Surround with try/except to catch any exceptions that may occur
                try:
                    # Wait for the user to add a reaction
                    reaction, user = await self.bot.wait_for('reaction_add', check=emoji_check)
                except Exception as ex:
                    print(ex)
                    return
                else:
                    if str(reaction.emoji) == "✅":
                        self.anon = True

                        # Delete the old embed
                        await Anon_or_Not.delete()

                        # Tell the user to type their mail into the chat
                        instructions = await user_channel.send(embed=SendInstructions(member))

                        # Making sure that the reply is from the author
                        def check(m):
                            return m.author == payload.member and user_channel.id == instructions.channel.id

                        # Wait for the message from the author
                        msg = await self.bot.wait_for('message', check=check)

                        # Making sure that the message is below 50 characters and the message was sent in the channel
                        while len(msg.content) < 50 and msg.channel == user_channel:
                            await user_channel.send(embed=ErrorHandling(member))

                            # Wait for the message from the author
                            msg = await self.bot.wait_for('message', check=check)

                        # As long as the message is above 50 characters and in the correct channel
                        if len(msg.content) > 50 and msg.channel == user_channel:
                            # Delete the previous embed
                            await instructions.delete()

                            # Determine a path for the message logs to be stored
                            path = "cogs/modmail/Anon.txt"
                            with open(path, 'a+') as f:
                                # Store the date and content of every message in the text file
                                async for message in user_channel.history(limit=300):
                                    print(f"{message.created_at} : {message.content}", file=f)

                            # Send the message to the modmail channel
                            await modmail_channel.send(embed=SendMsgToModMail(self, msg, member),
                                                       file=File(fp=path))

                            # Removing file from the directory after it has been sent
                            if os.path.exists(path):
                                os.remove(path)
                            else:
                                print("The file does not exist")

                            # Make sure the user knows that their message has been sent
                            await user_channel.send(embed=MessageSentConfirmation(member))

                            # Let the user read the message for 5 seconds
                            await asyncio.sleep(5)

                            # Delete the channel and then stop the function
                            await user_channel.delete()
                            return

                        # If the user types anywhere else, delete the channel
                        else:
                            await user_channel.delete()
                            return

                    if str(reaction.emoji) == "❌":
                        self.anon = False

                        # Delete the old embed
                        await Anon_or_Not.delete()

                        # Tell the user to type their mail into the chat
                        instructions = await user_channel.send(embed=SendInstructions(member))

                        # Making sure that the reply is from the author
                        def check(m):
                            return m.author == payload.member and user_channel.id == instructions.channel.id

                        # Wait for the message from the author
                        msg = await self.bot.wait_for('message', check=check, timeout=300)

                        # Making sure that the message is below 50 characters and the message was sent in the channel
                        while len(msg.content) < 50 and msg.channel == user_channel:
                            await user_channel.send(embed=ErrorHandling(member))

                            # Wait for the message from the author again
                            msg = await self.bot.wait_for('message', check=check, timeout=300)

                        if len(msg.content) > 50 and msg.channel == user_channel:
                            # Delete the previous embed
                            await instructions.delete()

                            # Determine a path for the message logs to be stored
                            path = "cogs/modmail/{}.txt".format(payload.member.name)
                            with open(path, 'a+') as f:
                                # Store the date and content of every message in the text file
                                async for message in user_channel.history(limit=300):
                                    print(f"{message.created_at} : {message.content}", file=f)

                            # Send the message to the modmail channel
                            await modmail_channel.send(embed=SendMsgToModMail(self, msg, member),
                                                       file=File(fp=path))

                            # Removing file from the directory after it has been sent
                            if os.path.exists(path):
                                os.remove(path)
                            else:
                                print("The file does not exist")

                            # Make sure the user knows that their message has been sent
                            await user_channel.send(embed=MessageSentConfirmation(member))

                            # Let the user read the message for 5 seconds
                            await asyncio.sleep(5)

                            # Delete the channel and then stop the function
                            await user_channel.delete()
                            return

                        # If the user types anywhere else, delete the channel
                        else:
                            await user_channel.delete()
                            return

            except Exception as ex:
                print(ex)

                # Removing file from the directory after it has been sent
                if os.path.exists(path):
                    os.remove(path)
                else:
                    print("The file does not exist")

                # Send out an error message if the user waited too long
                await user_channel.send(
                    "Sorry! Something seems to have gone wrong and the modmail will be aborting."
                    "\nRemember to make sure it's under **1024** characters!!")

                await asyncio.sleep(5)
                await user_channel.delete()


def setup(bot):
    bot.add_cog(Modmail(bot))