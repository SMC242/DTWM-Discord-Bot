#authors: benmitchellmtb, ScreaminSteve, FasterNo1
from discord import *
from discord.ext import commands
import threading, time, random, asyncio, time, inspect, traceback, string, unicodedata
import datetime as D
from typing import *

from classes import *

bot=commands.Bot(command_prefix="ab!", help_command=None, case_insensitive=True)
bot.add_cog(botOverrides(bot))

SCHEDULING_RAN = False

if __name__=="__main__":
    with open("Text Files/token.txt") as f:
        line=f.readline()
        token=line.strip("\n")


async def checkRoles(members: List[Member], target: List[Union[Role, str]])-> Union[bool, Generator[int, Tuple[bool, Member], None]]:
    '''Generator checker if the Member is an outfit member

    members: the target member(s)
    target: the target role(s). Maybe be the name or the Role instance
        
    RETURNS
    AsyncGenerator if multiple members
    If generator returned, the Member associated with the check is also returned:
    True(, Member): has target role
    False(, Member): does not have target role'''

    async def getRoles(members: List[Member], target: Union[List[str], List[Role]])-> List[Union[List[str], List[Role]]]:
        #made coro to speed up performance
        roles=[]

        if isinstance(target[0], str):  #if role name passed
            for member in members:
                currentRoles=[member.roles[i].name for i in range(0, len(member.roles))]
                roles.append(currentRoles)

        else:  #if Role instance passed
            for member in members:
                roles.append(member.roles)

        return roles

    async def generator(members: List[Member], roles: Union[List[str], List[Role]])-> Generator[int, Tuple[bool, Member], None]:
        hitMembers=[]

        for i in range(0, len(members)-1):
            success=False
            for role in target:
                if role in roles[i] and members[i] not in hitMembers:
                    yield (True, members[i])
                    hitMembers.append(members[i])  #stop the same person being hit 2 times if has multiple target roles

            if not success:  #if not target
                yield (False, members[i])


    #fetch roles
    roles=await getRoles(members, target)

    #do check
    isList=len(members)>1

    if isList:  #if list of members: return generator
        return generator(members, roles)

    else:  #if single member: return bool
        success=False
        for role in target:
            if role in roles[0]:
                return True

        return False #if not target


def isLeader():
    '''Decorator to allow only leaders to call the command'''
    async def inner(ctx):
        #checking if the user is a leader
        success= await checkRoles((ctx.message.author,), ("Watch Leader", "Champion"))

        if not success:
            raise NotLeaderError()

        return success

    return commands.check(inner)


def inBotChannel():
    '''Checks if called in bot channel.
    If not in bot channel, doesn't execute command and scolds.
    Unless command is whitelisted'''

    async def inner(ctx):
        botChannel=ctx.bot.get_channel(545818844036464670)

        if not botChannel==ctx.message.channel:
            await ctx.send(f"These are matters for {botChannel.mention}, brother. Take it there and I will answer you")
            return False

        else:
            return True

    return commands.check(inner)

@bot.group()
@isLeader()
async def leader(ctx):
    if ctx.invoked_subcommand is None:
        return await ctx.send('Give me your orders, My Lord. I am but a lowly servitor, not a psyker')


@bot.command(aliases=["h"])
@inBotChannel()
@commands.cooldown(1, 10, type=commands.BucketType.user)
async def help(ctx):
    '''Displays all of the commands'''

    print("Command: help call recieved")

    #sort commands alphabetically
    filterOut=commands.Group
    notGroup={command.name : command for command in bot.walk_commands() if not isinstance(command, filterOut)}  #filter out Groups

    botCommands=[notGroup[key] for key in sorted(notGroup)]

    #show main and leader commands in separate messages
    mainMessage=Embed(title="Help - Main Commands", description="All of the commands of Inquisition. Invoke with ab!{commandName}",\
       colour=Colour(13908894))

    mainMessage.set_thumbnail(url="https://images-ext-1.discordapp.net/external/3K5RIK7FKfthdHJl0ubKh8uUSKjEP8odoO4ks1evlzs/%3Fsize%3D128/https/cdn.discordapp.com/avatars/507206805621964801/3468cd3ed831a5b10b49d8e06c801418.png")

    leaderMessage=Embed(title="Help - Leader Commands",\
       description="Leader only commands. Invoke with ab!leader {commandName}\n>=Champion only",\
       colour=Colour(13908894))

    #iterate over all commands
    hitCommands=[]
    for command in botCommands:
        #check if leader command
        if command not in hitCommands:
            if isinstance(command, commands.Group):  #ignore groups
                    continue

            elif command.parent is None:  #if ungrouped command
                msg=mainMessage

            elif command.parent.name=="leader":  #if leader command
                msg=leaderMessage

            response=f"{command.help}\nAliases: {command.aliases}"

            #display enabled status
            if not command.enabled:  #don't say when enabled
                response+="\n**Currently disabled**"

            #add text to final message
            msg.add_field(name=command.name, value=response, inline=False)
            hitCommands.append(command)

        else:
            continue

    await ctx.send(embed=mainMessage)
    return await ctx.send(embed=leaderMessage)


@leader.command(aliases=['re', 'noRe', 'reactions', 'TR', 'nR'])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def toggleReactions(ctx):
    '''Allow/disallow reactions to messages with terms in the white list'''

    print("Command: toggleReactions call recieved")

    botOverride=bot.get_cog('botOverrides')
    botOverride.reactionParent.reactionsAllowed = not botOverride.reactionParent.reactionsAllowed

    return await ctx.send(f"I {'will' if botOverride.reactionParent.reactionsAllowed else 'will not'} react to messages, My Lord")

@inBotChannel()
@leader.command(aliases = ["away", ])
async def markAsAway(ctx, name: str):
    """Mark a person as away. 
    Arguments: ab!leadermarkAsAway {name}
    name: Their player name"""

    await ctx.send("It will be done, My Lord.")
    async with ctx.typing():
        cog_ = bot.get_cog("AttendanceDBWriter")
        await cog_.markAsAway(name)
        return await ctx.send("He has been excused. May he return to battle soon.")


@inBotChannel()
@leader.command()
async def removeMember(ctx, name: str):
    """Unregister the target member.
    Arguments: ab!leader removeMember {name}
    name: Their player name."""

    await ctx.send("It will be done, My Lord.")
    async with ctx.typing():
        cog_ = bot.get_cog("AttendanceDBWriter")
        await cog_.deleteMember(name)
        return await ctx.send("Another brother wrenched away by Chaos...")


@inBotChannel()
@leader.command()
async def addMember(ctx, name: str):
    """Register the target member.
    Arguments: ab!leader addMember {name}
    name: Their player name."""

    await ctx.send("It will be done, My Lord.")
    async with ctx.typing():
        cog_ = bot.get_cog("AttendanceDBWriter")
        await cog_.addMember(name)
        return await ctx.send(f"Welcome to the chapter, brother {name}!")


@leader.command(aliases=["V5", "INeedARide", "WaitUpLetMeHopIn"])
@inBotChannel()
async def getInOps(ctx):
    '''Pings every member that's playing PS2 but isn't in ops comms.'''
    print("Command: getInOps call recieved")
    await getInOpsInner()


async def getInOpsInner():
    def inEventChannel(member: Member, channels: List[VoiceChannel])->bool:
        #verifying that they're in a channel
        if member.voice is None:
            return False

        else:
            #checking if they're in an event channel
            return member.voice.channel in channels

    botChannel=bot.get_channel(545818844036464670)

    async with botChannel.typing():
        #get the server
        server=bot.get_guild(545422040644190220)

        #get list of Members >=Astartes
        members=[]
        async for check, member in await checkRoles(server.members, ("Astartes", "Watch Leader")):
            if check:
                members.append(member)
    
        #get members playing PS2
        membersInPS2=[]
        for member in members:
            for activity in member.activities:
                if activity.name=="PlanetSide 2":
                    membersInPS2.append(member)
        
        #get event channels
        channels=createListFromFile("channels.txt", type=int)

        eventChannels=[bot.get_channel(channelID) for channelID in channels]

        #check if in event channels
        for member in membersInPS2:
            inEvent=inEventChannel(member, eventChannels)

            if not inEvent:
                await botChannel.send(f'{member.mention} an event is running right now, brother. Come join us in glory!')

        return "Nya~"  #end typing()


async def reactToOutput(ctx: commands.Context, responses: Dict[Tuple[int, int], str], toCompare: int,
    message: str=None, defaultResponse: str="", **relevantVars):
    '''Sends a message from responses based on output.
    If output is not in responses' keys, defaultResponse will be outputted.

    responses: should be in this format:
        range of values(min, max) : message to send.
        The same value can be placed twice e.g (1, 1) for toCompare to be required to hit that value.
    toCompare: the output of the command that calls this function. Compared against the ranges in responses.
    message: the message from the command. The response will be appended to this
    defaultResponse: what will be sent if output meets none of responses' criteria.
    **relevantVars: any variables needed for the message'''

    for comparisonRange, response in responses.items():
        if comparisonRange[0] <= toCompare <= comparisonRange[1]:
            return await ctx.send(message + response)

    #if toCompare not hit
    return await ctx.send(message + defaultResponse)


async def executeOnEvents(func: AsyncCommand, milestones: List[int]=None):
    '''Infinitely checks if the time now is during
   the event hours then executes the function if that's true.
   Uses UTC time.

   func: the AsyncCommand object to call on each milestone
   milestones: the UTC times to execute at'''

    print(f"Scheduled Event ({func.name}): beginning execution")

    varList=[]
    if milestones is None:
        milestones = createListFromFile("milestones.txt", type=int)

    while True:
        success=False

        timenow=int(D.datetime.now().strftime("%H%M"))

        #exit if out of event time
        if timenow> milestones[-1]:
            print("Scheduled Event ({func.name}): exited. Error: too late")
            return

        for milestone in milestones:  #check each 
            milestone=int(milestone)

            if milestone == int(timenow):
                print(f"Scheduled Event ({func.name}): milestone hit: {timenow}")
                success=True

                output= await func.call()

                for element in output:
                    if element not in varList:
                        varList.append(element)

                if timenow == milestones[-1]:
                    print(f"Scheduled event ({func.name}): execution finished")
                    return varList

                else:
                    try:
                        milestones.remove(milestone)  #to stop the milestone from being hit again

                    except ValueError:  #milestone already removed
                        pass

                await asyncio.sleep(35)     
        
        if not success:
            await asyncio.sleep(35)


@bot.command(aliases=["notMember", "notM"])
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def imNotAMember(ctx):
    '''Reacts to whether you're a member of DTWM'''
    print('Command: imNotAMember call recieved')

    if not await checkRoles((ctx.message.author,), ("Astartes", "Watch Leader")):
        await ctx.send('Join DTWM on Miller NC')
        return await ctx.invoke(joinDTWM)

    else:
        return await ctx.send("Brother, you are one of us!")


@bot.command(aliases=["pat", "headpat"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def patLoli(ctx):
    '''Get the bot to pat a loli'''

    emotes=[
        "<:w_komi_headpat:661011597048938505>",
        "<a:BTS_pat9:661014548970602506>",
        "<a:BTS_pat8:661014550396665856>",
        "<:BTS_pat7:661014545543856178>",
        "<:BTS_pat6:661014545791320104>",
       "<:BTS_pat5:661014545560764416>",
        "<:BTS_pat4:661014544860053504>",
        "<:BTS_pat3:661014543631253550>",
        "<a:BTS_pat2:661014549922578432>",
        "<a:BTS_pat12:661014546260951095>",
        "<:BTS_pat11:661014545795645443>",
        "<a:BTS_pat10:661014544944070656>",
        "<:BTS_pat:661014543765602314>",
        ]

    print("Command: patLoli call recieved")
    return await ctx.send(random.choice(emotes))


async def removeTitles(channelMembers: List[str]):
    '''Removes the titles after people's nicknames'''

    delimiters=createListFromFile("delimiters.txt")

    attendees=[]
    for name in channelMembers:
        newName = name
        for delimiter in delimiters:
            if delimiter in newName:
                newName, *null=newName.split(delimiter)
    
        attendees.append(newName)

    return attendees


async def getAttendance(ctx: Union[commands.Context, Guild])-> List[str]:
    '''Returns a list of people in the ops/training channels'''
    #reads the channels to check from a file
    #appends the channel IDs to channels
    channels=createListFromFile("channels.txt", type=int)

    #for every channel in channels it gets the members  
    #sequentially and appends them to the list

    #get guild
    if not isinstance(ctx, Guild):
        server=ctx.message.guild

    else:
        server=ctx
    
    #get list of names in ops
    channelMembers=[]
    for channel in channels:
        channel=server.get_channel(channel)

        for attendee in channel.members:
            channelMembers.append(attendee.display_name)


    #parsing the names
    attendees = await removeTitles(channelMembers)

    print(f"Attendees at {D.datetime.now().strftime('%H%M')}: {attendees}")

    return attendees

async def callAttendance(attendees: List[str])-> bool:
    '''Wrapper for writeattendance. Handles attendance being called on a Saturday.
    
    RETURNS
    False: if no failure
    True: if failure'''

    DBWriter=bot.get_cog('AttendanceDBWriter')
    try:
        await DBWriter.sendAttToDB(attendees)
        return False

    except:
        return True


async def attendanceWrapper(ctx):
    '''This wrapper exists so that attendance can be called outside of doAttendance
    as doAttendance is a command object'''
    attendees=await getAttendance(ctx)

    failure= await callAttendance(attendees)

    return attendees, failure


@bot.command(aliases=["weeb"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def ayaya(ctx):
    '''Tell the bot to be a weeb'''

    print("Command: ayaya call received")
    responses=[
        "ayaya!",
        "AYAYA!",
        "ayaya ayaya!",
        "AYAYA AYAYA!",
        "ayaya ayaya ayaya!",
        "AYAYA AYAYA AYAYA!"]

    await ctx.send(random.choice(responses))


@bot.command(aliases=["kys","die", "fuckYou"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def commitNotAlive(ctx):
    '''Tell the bot to kill itself'''
    print("Command: commitNotAlive call recieved")

    responses=[
        "no u",
        "commit neck rope",
        "die",
        "kys"
        ]
    
    await ctx.send(random.choice(responses))
    

@leader.command(aliases=["attendance","getAttendance", "att"])
@inBotChannel()
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def doAttendance(ctx):
    '''Records current attendees in the db.'''

    print("Command: doAttendance call recieved")
    
    #give user feedback
    await ctx.send("It will be done, my Lord")

    async with ctx.typing():
        attendees, failure=await attendanceWrapper(ctx)

        if failure:
            await ctx.send('We do not take roll call on Saturdays!')

        if attendees==[]:
            await ctx.send("Nobody is there, My Liege. Our men have become complacent!")

        else:
            await ctx.send(f"Attendees: {attendees}")

        await ctx.send("Attendance check completed **UmU**")



@bot.command(aliases=["advice", "advise", "adviseMe"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def giveAdvice(ctx, target: str=None):
    '''Gives you advice based on your roles
    If you're a scout you will get mostly useful advice
    Arguments: ab!giveAdvice {target}
        **[optional]** the target role'''

    print("command: giveAdvice call recieved")

    mainRoleResponses={
        "watch commander" : ["Learn to split <:splitwatch_marines:618120678708609054>",
                             "Become a dictator",
                             "Make good outfit EZ",
                             "If you don't have 70 KPM you can't be a leader 😤",
                             "Disband.",
                             ],

        "watch leader" : ["Why haven't you split yet?",
                          "Just zerg",
                          "Get more zerglings",
                          "Get a life",
                          "MMO mice are good investments",
                          "Recruit plox",
                          "Remember to take breaks from leading or you'll get burnt out"
                          ],

        "watch captain" : ["Just get promoted lmao",
                           "Shhh don't tell ben: his hentai stash is at ---- Fuck he's coming! Help!",
                           "Get some sleep 👀"
                           ],

        "champion" : [
            "Just get promoted lol",
            "This is tankistrole get out!",
            "Recruit plox",
            "Go mentor someone",
            "You have done well youngling... Your splitting power has grown but you're not there yet... Become a Watch Leader",
            "You can't be a mentor if you've used a shotgun for 0.001% of your play time 😤"
            ],
            
        "keeper" : ["Green = gay lol",
                    "Go ask a >= Champion for training",
                    "Git gud",
                    "Get in zergling; we have a continent to cap!"
                    "Remember to V5 after killing good players",
                    "Teamkill best kill 😉"],

        "scout" : [
            "You can ask anyone >= Champion for advice, mentorship, and 1 to 1 training",
            "Do your basic trainings",
            "Come to ops on Thursdays, Fridays, and Sundays at 2100 CEST",
            "We have trainings from Monday to Wednesday at 2100 CEST. Come along!",
            "Avoid cluttering comms", 
            "Remember to use cardinal directions not relative callouts! Use the format: '[cardinal direction/building call out] [target type]"
            f"You can get access to the meme and not safe for life channel by typing .iam heretic in {ctx.bot.get_channel(545818844036464670).mention}",
            "To get promoted, you need to attend all 3 basic trainings and be noticed by >= Keepers as well-integrated into the community",
            f"You may seek knowledge in our chapter's {ctx.bot.get_channel(551905489236000794).mention} . Training docs will be pinned"
            ],

        "battle brother" : [
            "Come along to the joint ops with your outfit on Thursdays/Fridays at 2100 CEST",
            "Friendship is great ❤ come join us in voice channels",
            "You can join any of our ops on Thursdays, Fridays, and Sundays"
            ],
        
        "guardsman" : [
            "Join DTWM",
            "You can join our ops on Thursdays and Fridays at 2100 CEST to get a taster of our play",
            "Come hang out in the NC channel"
            ],
        }

    extraRoleResponses={
        "everyone" :[
            "V1",
            "V2",
            "V3",
            "I need repairs!",
            "V4",
            "V5",
            "V5",
            "V5",
            "I need a ride",
            "Wait up! Let me hop in!",
            "V6", 
            "V7", 
            "V8",
            "V9",
            "V0",
            "I need a gunner!",
            "Somebody hop in!!"
            ],

        "remembrancer" :[
            "Make something pretty for us, loyal Remembrancer",
            ],

        "primarch" :[
            f"You can find all relevant information to our co-ops pinned in {ctx.bot.get_channel(645695680731414578).mention}",
            ],

        "heretic" :[
            "HERESY DETECTED! COMMENCE VIRUS BOMBING!",
            "I see you're a man of culture",
            f"Post something weird in {ctx.bot.get_channel(545809293841006603).mention}"
            ],

        "nitro booster" : [
            "Thanks for boosting! You are a loyal son of the Emperor",
            "MMM here's a sloppy kiss just for you 💋 Thanks for boosting!"
            ]

        }

    await ctx.send("*Thinking...*")

    #displays a typing indicator while this happens
    async with ctx.typing(): 

        #check if bot is responding to itself
        if ctx.message.author!=bot.user.id: 

            if target is not None:
                return await ctx.send(random.choice(mainRoleResponses[target.lower()]))

            roleNames=[ctx.message.author.roles[i].name.lower()\
               for i in range(0, len(ctx.message.author.roles))]

            responseCount=0
            responseCountExtra=0

            while responseCount==0 and responseCountExtra==0:

                #check each supported role against the invoker's roles
                for role in list(mainRoleResponses.keys()): 
                
                    #limit the responses to up to 4
                    if role in roleNames and responseCount<2: 

                        if role=="scout":
                            await ctx.send(f"You will get serious advice as you are new here:\n{random.choice(mainRoleResponses[role])}")

                        #1/2 chance to say something per role so that less messages are sent
                        elif random.choice([True, False]):
                            await ctx.send(random.choice(mainRoleResponses[role]))
                            responseCount+=1      
                            
                    elif responseCount==2:
                        return

                #same as main but for extra roles
                responseCountExtra=0
                for role in list(extraRoleResponses.keys()):
                    if role in roleNames and responseCountExtra<1:
                        if random.choice([False, False, True]):  #1/3 chance to respond

                            await ctx.send(random.choice(extraRoleResponses[role]))

                            responseCountExtra+=1

                    elif responseCountExtra==1:
                        return


@bot.command(aliases=["join", "j"])
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def joinDTWM(ctx):
    '''Posts the invite link to the discord'''
    print("Command: joindtwm call recieved")
    await ctx.send('Come quickly, brother! We can always use new Astartes. https://joindtwm.net/join')


@bot.command(aliases=["fun", "random"])
@inBotChannel()
#@commands.cooldown(1, 10, type=commands.BucketType.user) 
async def fluff(ctx):
    '''Picks a random fluff command and executes it'''

    fluff=[
        imNotAMember,
        patLoli,
        ayaya,
        commitNotAlive,
        giveAdvice,
        ping,
        ]

    print("Command: fluff call recieved")

    async with ctx.typing():
        choice=random.choice(fluff)
        await ctx.send(f"{choice}:")

        return await ctx.invoke(choice)


@bot.command(aliases=['count', 'cm', 'getMessages'])
@inBotChannel()
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def countMessages(ctx, name: str):
    '''Returns and reacts the number of messages in the target channel.
    Counts today's messages only.
    Arguments: ab!countMessages {name}
    #mention a text channel or 'global' for the whole discord'''

    async def getAllMessages(channel):
        history=channel.history(limit=5000, after=after)  #HistoryIterator isn't iterable (╯°□°）╯︵ ┻━┻

        count = 0
        #iterate over messages
        while count!=5000:  #ensuring that no more than 5k messages are processed
            try:
                await history.next()
                count+=1

            except NoMoreItems:
                break

            except Forbidden:  #ignore channels that the bot can't read
                continue

        return count


    print("Command: countMessages call recieved")

    async with ctx.typing():
        server=None
        try:
            if name=="global":
                server=ctx.bot.get_guild(545422040644190220)
            
            else:
                channel=ctx.message.channel_mentions[0]

        except:
            raise commands.MissingRequiredArgument(inspect.Parameter("name", inspect.Parameter.POSITIONAL_ONLY))

        #create filter
        after=D.datetime.today() - D.timedelta(1)

        #get messages today
        count=0

        if server is None:
            count = await getAllMessages(channel)

        else:  #if global check
            for channel in server.text_channels:
                count += await getAllMessages(channel)
        

        #reacting
        if server is not None:  # if global
            responses={
                (0, 800) : "A quiet day aboard the Erioch",
                (800, 1400) : "A mild hull breach occurred. It's fixed now, My Lord",
                (1400, 1500) : "Maintenance in the engine room occurred today. Many souls were lost",
                (1500, 1600) : "We were planning to make war"
            }

            return await reactToOutput(ctx, responses, count,\
                f"Status report, Sir: {count} messages were conveyed across our glorious vessel. ",\
                "We suffered an Eldar incursion")

        else:  # if channel
            responses={
                (0, 100) : "Not much happened, My Lord",
                (100, 200) : "The Guardsmen were arguing again",
                (400, 500) : "A minor brawl. Nothing too serious, My Lord",
                }

            return await reactToOutput(ctx, responses, count, \
                f"Status report, Sir: {count} messages were sent today in {channel.mention}. ",\
                "Chaos cultists were uprooted from their despicable congregation")


@bot.command(aliases = ["CR"])
@inBotChannel()
async def countReactions(ctx, name):
    '''Counts all reactions in the target channel.
    Arguments: ab!countReactions {name}
        name: #mention a channel or global for the entire discord'''

    async def getChannelReactions(channel):
        history=channel.history(limit=5000, after=after)  #HistoryIterator isn't iterable (╯°□°）╯︵ ┻━┻

        count = 0
        #iterate over messages
        while count!=5000:  #ensuring that no more than 5k messages are processed
            try:
                msg = await history.next()
                for reaction in msg.reactions:
                    count+=1

            except NoMoreItems:
                break

            except Forbidden:  #ignore channels that the bot can't read
                continue

        return count


    print("Command: countReactions call recieved")

    async with ctx.typing():
        server=None
        try:
            if name=="global":
                server=ctx.bot.get_guild(545422040644190220)
            
            else:
                channel=ctx.message.channel_mentions[0]

        except:
            raise commands.MissingRequiredArgument(inspect.Parameter("name", inspect.Parameter.POSITIONAL_ONLY))

        #create filter
        after=D.datetime.today() - D.timedelta(1)

        #get messages today
        count=0

        if server is None:
            count = await getChannelReactions(channel)

        else:  #if global check
            for channel in server.text_channels:
                count += await getChannelReactions(channel)

        #give feedback
        if server is None:
            return await ctx.send(f"{count} reactions were given today in {channel.mention}, My Lord")

        else:
            return await ctx.send(f"{count} reactions were given today, My Lord")


@bot.command(aliases=["p", "speed"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def ping(ctx):
    '''Check and react to how fast the bot is running'''

    async with ctx.typing():
        #get difference
        startTime=time.time()
        await ctx.send('You summoned me, my Lord?')
        endTime=time.time()
        difference=endTime-startTime

        #react to result
        responses={
            (0, 0.1) : "I came as fast as I could",
            (0.1, 0.5) : "I polished your armour",
        }

        print(f"Command: ping call recieved.\n   Process time: {difference} seconds\n   Latency: {bot.latency}")
        return await reactToOutput(ctx, responses, difference,\
           f"Latency: {bot.latency:.2f}\nI took {difference:.2f} seconds to get here. ",\
           "The Tyranids are coming! You must escape now and send word to Terra")


@leader.command(aliases=["nig", "blue", "BLA", "BLATT", "B"], enabled = False)
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def markAsBlue(ctx, days: int=1, *target):
    '''Marks the target on the sheet as blue for X number of days.
    Arguments: ab!leader markAsBlue {days} {target}
        days = number of days to mark as blue. Defaults to 1
        target = copy the FULL nickname of the member
        '''
    #target: Tuple[str]

    async def stripTag(name: str)-> str:
        '''Strips out [TAG]s with a linear search.'''

        if "]" in name:
            #linear search for end of outfit tag and set name to name after tag
            i=0
            while True: 
                if name[i] == "]":
                    try:
                        if name[i+1]==" ":  #some people put spaces
                            i+=1

                        return name[i+1:]

                    except IndexError:  #tag at end of name
                        return name

                else:
                    i+=1

        else:
            return name


    async def removeSymbols(name: str)-> str:
        '''Remove all the weird shit from people's names'''
        letters=string.ascii_letters

        for char in name:
            if char not in letters:
                name=name.replace(char, "")

        return name

    async def genocide(names: List[str]) -> List[str]:
        '''Attempts to fix all the people with stupid names, removes them if too stupid'''
        #credit to Auroram for rewrite

        noTags = [await stripTag(name) for name in names]

        #try to save them - convert accents to latin letters
        latinNames = [unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')\
            for name in noTags]

        #remove all surviving stupid characters
        asciiNames = [name.encode('ascii', 'ignore') for name in latinNames]

        #delete people whose names were all taken out
        return list(asciiNames.filter("", asciiNames))


    print("Command: markAsBlue call recieved")
    await ctx.send("Yes, My Lord")

    async with ctx.typing():
        #check args
        if target is None or not any(target):
            raise commands.MissingRequiredArgument(inspect.Parameter("target", inspect.Parameter.POSITIONAL_ONLY))

        if days<=0:
            raise commands.BadArgument(inspect.Parameter("days", inspect.Parameter.POSITIONAL_ONLY))

        #rebuild name
        originalName = "".join(target)  #stored for later 
        targetName=originalName.lower()
        targetName= await stripTag(targetName)
        targetName = await removeSymbols(targetName)
    
        # verifying that the target exists
        #create dict of members with letter-only names
        names={}
        for person in ctx.guild.members:
            name=person.display_name.lower()

            name=await stripTag(name)

            name = await removeSymbols(name)

            names[name] = person

        sortedNames=sorted(names)  #sort names into list

        exists=binarySearch(targetName, sortedNames, False)
        if not exists:  #they don't exist
            return await ctx.send("That person does not exist, My Lord")

        else:
            person=names[targetName]

        #verifying that they're a member
        if not await checkRoles((person,), ("Astartes", "Champion", "Watch Leader")):
            return await ctx.send("That person is not one of ours, My Lord")

        #send to sheet
        botOverride=bot.get_cog('botOverrides')
        targetName = await removeTitles( (originalName, ) )

        try:
            await botOverride.sheetHandler.markAsBlueOnSheet(*targetName, days)

        except ValueError as error:
            return await ctx.send("He is unknown to us... *Hush, My Lord... We may have a Genestealer among us*")

        return await ctx.send("His absence has been excused, My Lord")


@leader.command(aliases=["CS"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def changeStatus(ctx, status: str):
    '''Changes the status to the target status name.
    Will be overridden within an hour by the normal status loop.
    Arguments: ab!leader changeStatus {name}
        newVideo: new youtube video is being uploaded
        eventSoon: event in < 1 hour
        gathering: gathering in < 1 hour
        meeting: leaders in meeting, do not disturb
        shitstorm: drama
        chaos: weird stuff in forbidden knowledge'''

    async def getLastFKMessage():
        '''Gets the link to the most recent message of Forbidden Knowledge'''

        #could be done in 1 line if last_message was reliable
        FK = bot.get_channel(545809293841006603)
        messages = await FK.history(limit=1).flatten()

        return messages[0].jump_url


    print("Command: changeStatus call recieved")

    types: Dict[str, Tuple[str, Optional[str], Optional[str], ActivityType]] = {
        "newvideo": ("New propaganda on our channel", "https://tinyurl.com/dtwmyt", None, ActivityType.playing),

        "eventsoon" : ("Ops soon. Hop in comms, brother", None, None, ActivityType.playing),

        "gathering" : ("Astartes gathering soon. Get in comms, brother", None, None, ActivityType.playing),

        "meeting" : ("Hush, the Watch Leaders are planning", None, None, ActivityType.playing),

        "shitstorm" : ("The Drama", None, bot.get_channel(545817822870110208).mention, ActivityType.watching),  #guardsman hub

        "chaos" : ("Disrupting A Cultist Ritual", None, bot.get_channel(545809293841006603).mention, ActivityType.playing),  #forbidden knowledge
    }

    try:
        msg, link, body, activity = types[status.lower()]

    except KeyError:
        raise commands.BadArgument(inspect.Parameter("days", inspect.Parameter.POSITIONAL_ONLY))

    #create embed
    response=Embed(title=msg, url=link, colour=Colour(13908894))

    #these won't work as __init__ args for some reason
    response.set_thumbnail(url = "https://images-ext-1.discordapp.net/external/3K5RIK7FKfthdHJl0ubKh8uUSKjEP8odoO4ks1evlzs/%3Fsize%3D128/https/cdn.discordapp.com/avatars/507206805621964801/3468cd3ed831a5b10b49d8e06c801418.png")

    #send response and change status
    await ctx.send(content = body, embed=response)
    return await bot.change_presence(activity = Activity(name = msg, type = activity))


@bot.command(aliases=["week", "whatTraining", "trainingWeek", "armourOrAir"])
@inBotChannel()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def getTrainingWeek(ctx):
    '''Returns whether this week is armour or air trainings on Monday + Tuesday'''

    print("Command: getTrainingWeek call recieved")

    botOverride=bot.get_cog('botOverrides')

    try:
        return await ctx.send(f"This week, we will train for {botOverride.trainingWeek}, Brother")

    except ValueError:  #if firstTrainingWeek is not a Monday
        return ctx.send("My archives are corrupt! Please report this to the Adepts immediately")


async def scheduleAttendance():
    
    # prevent duplicate queues
    global SCHEDULING_RAN

    # check if it's a new day
    today = D.datetime.today().date().day
    botOverride = bot.get_cog("botOverrides")
    if botOverride.startDay.day != today:
        # reschedule and update the starting day
        SCHEDULING_RAN = False
        botOverride.startDay = today

    if SCHEDULING_RAN:  
        return

    else:
        SCHEDULING_RAN = True
        # remove once this comes out of the testing phase
        await bot.get_channel(545818844036464670).send("```css\nTemporary logging: Attendance scheduled```")

    #scheduling the attendance function
    timenow=D.datetime.now()
    if timenow.weekday() == 5:  #no events on Saturday
        return

    timenow=timenow.time()

    if 2000<int(timenow.strftime("%H%M"))<2130:  #if started during an event
        attendees=await executeOnEvents(AsyncCommand(getAttendance, name="getAttendance", arguments=(bot.get_guild(545422040644190220),)))
        try:
            failure=await callAttendance(attendees)

        except TypeError:  #event started too late
            pass

        if failure:
            pass

    else:  #wait until almost event time
        target=D.time(19, 59)
    
        newTarget=D.datetime.combine(D.date.min, target)
        oldTime=D.datetime.combine(D.date.min, timenow)
        runInSeconds= (newTarget - oldTime).seconds

        await asyncio.sleep(runInSeconds)

        await getInOpsInner()  #ping people to get in ops

        attendees=await executeOnEvents(AsyncCommand(getAttendance, name="getAttendance", arguments=(bot.get_guild(545422040644190220),)))
        try:
            failure= await callAttendance(attendees)

        except TypeError:  #event started too late
            pass

        if failure:
            pass


@bot.listen()
async def on_ready():
    print('\nLogged in as')
    print(f"Username: {bot.user.name}")
    print(f"User ID: {bot.user.id}")
    print('------')

    #acknowledge startup
    botChannel=bot.get_channel(545818844036464670)
    await botChannel.send('I have awoken... I am at your service')

    #set up on_message with the channel list
    botOverride=bot.get_cog('botOverrides')
    await botOverride.reactionParent.getChannels()

    #start random statuses
    loop=asyncio.get_event_loop()
    loop.create_task(botOverride.chooseStatus())

    # schedule attendance
    await scheduleAttendance()

if __name__=="__main__":
    commandListener(bot)
    bot.run(token)