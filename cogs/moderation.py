import asyncio
import datetime
from datetime import timedelta
from typing import Optional

from discord import Member, Embed
from discord.ext import commands
from discord.ext.commands import command, guild_only, has_guild_permissions, bot_has_guild_permissions, Greedy, \
    has_permissions, bot_has_permissions, cooldown, BucketType

from settings import enso_embedmod_colours

# Store guildID's and modlog channel within a cached dictionary
modlogs = {}


async def kick_members(message, targets, reason):
    for target in targets:
        if (message.guild.me.top_role.position > target.top_role.position
                and not target.guild_permissions.administrator):
            await target.kick(reason=reason)

            embed = Embed(title="Member Kicked",
                          colour=enso_embedmod_colours,
                          timestamp=datetime.datetime.utcnow())

            embed.set_thumbnail(url=target.avatar_url)

            fields = [("Member", f"{target.mention}", False),
                      ("Actioned by", message.author.mention, False),
                      ("Reason", reason, False)]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            return embed


class Moderation(commands.Cog):
    """Moderation Commands! (Kick/Ban/Mute etc)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")

    @commands.group()
    @has_permissions(manage_guild=True)
    @bot_has_permissions(administrator=True)
    @cooldown(1, 1, BucketType.user)
    async def modlogs(self, ctx):
        pass

    @command(name="kick", aliases=["Kick"], usage="`<member>` `[reason]`")
    @guild_only()
    @has_guild_permissions(kick_members=True)
    @bot_has_guild_permissions(kick_members=True)
    @cooldown(1, 1, BucketType.user)
    async def kick_member(self, ctx, members: Greedy[Member], *, reason: Optional[str] = "No Reason Given"):
        """Kick Members from Server"""

        # Make sure member(s) are entered properly
        if not len(members):
            message = await ctx.send(
                f"Not Correct Syntax!"
                f"\nUse **{ctx.prefix}help** to find how to use **{ctx.command}**")

            # Let the user read the message for 5 seconds
            await asyncio.sleep(5)
            # Delete the message
            await message.delete()

        # As long as all members are valid
        else:

            # Send embed of the kicked member
            embed = await kick_members(ctx.message, members, reason)
            message = await ctx.send(embed=embed)

            # Let the user read the message for 10 seconds
            await asyncio.sleep(10)
            # Delete the message
            await message.delete()

    @command(name="ban", aliases=["Ban"])
    @guild_only()
    @has_guild_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    @cooldown(1, 1, BucketType.user)
    async def ban(self, ctx, member: Member, *, reason=None):
        """Ban Members from Server"""

        # Check if reason has been given
        if reason:
            reason = reason
        # Set default reason to None
        else:
            reason = "No Reason Given"

        # Ban the user and send confirmation to the channel
        await ctx.guild.ban(user=member, reason=reason)
        await ctx.send(f"{ctx.author.name} **banned** {member.name}"
                       f"\n**Reason:** '{reason}'")

    @command(name="unban", aliases=["Unban"])
    @guild_only()
    @has_guild_permissions(ban_members=True)
    @bot_has_guild_permissions(ban_members=True)
    @cooldown(1, 1, BucketType.user)
    async def unban(self, ctx, member: int, *, reason=None):
        """Unban Member from Server"""

        # Check if reason has been given
        if reason:
            reason = reason
        # Set default reason to None
        else:
            reason = "No Reason Given"

        # Get the member and unban them
        member = await self.bot.fetch_user(member)
        await ctx.guild.unban(member, reason=reason)

        # Confirm that the user has been unbanned
        await ctx.send(f"{ctx.author.name} **unbanned** {member.name}"
                       f"\n**Reason:** '{reason}'")

    @command(name="purge", aliases=["Purge"])
    @guild_only()
    @has_guild_permissions(manage_messages=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    @cooldown(1, 1, BucketType.user)
    async def purge(self, ctx, amount: int = None):
        """Purge Messages from Channel
        (No Amount Will Default to 50 Messages Deleted)"""

        # When an amount is specified and is between 0 and 100
        if amount:
            if 0 < amount <= 100:
                with ctx.channel.typing():

                    # Delete the message sent and then the amount specified
                    # (Only messages sent within the last 14 days)
                    await ctx.message.delete()
                    deleted = await ctx.channel.purge(limit=amount,
                                                      after=datetime.datetime.utcnow() - timedelta(days=14))

                    await ctx.send(f"Deleted **{len(deleted):,}** messages.", delete_after=5)

            # Send error if amount is not between 0 and 100
            else:
                await ctx.send("The amount provided is not between **0** and **100**")

        # Delete the last 50 messages if no amount is given
        else:

            # Delete the message sent and then the amount specified
            # (Only messages sent within the last 14 days)
            await ctx.message.delete()
            deleted = await ctx.channel.purge(limit=50,
                                              after=datetime.datetime.utcnow() - timedelta(days=14))

            await ctx.send(f"Deleted **{len(deleted):,}** messages.", delete_after=5)


def setup(bot):
    bot.add_cog(Moderation(bot))
