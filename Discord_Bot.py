#authors: benmitchellmtb, ScreaminSteve, FasterNo1
from discord import *
from discord.ext import commands
import threading, time, random, asyncio, time, inspect, traceback
import datetime as D
from typing import *

from classes import *
from sheet import *

bot=commands.Bot(command_prefix="ab!", help_command=None, case_insensitive=True)
bot.add_cog(botOverrides(bot))

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
    botOverride.reactionsAllowed= not botOverride.reactionsAllowed

    return await ctx.send(f"I {'will' if botOverride.reactionsAllowed else 'will not'} react to messages, My Lord")


@leader.command()
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

        for milestone in milestones:
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


async def getAttendance(ctx: Union[commands.Context, Guild]):
    '''Returns a list of people in the ops/training channels'''
    #reads the channels to check from a file
    #appends the channel IDs to channels
    channels=createListFromFile("channels.txt", type=int)
    delimiters=createListFromFile("delimiters.txt")

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
    attendees=[]
    for attendee in channelMembers:
        for delimiter in delimiters:
            try:
                attendee, *null=attendee.split(delimiter)

            except ValueError:  #if delimiter not in attendee
                pass

        attendees.append(attendee)

    print(f"Attendees at {D.datetime.now().strftime('%H%M')}: {attendees}")

    return attendees

def callAttendance(attendees: List[str])-> bool:
    '''Wrapper for writeattendance. Handles attendance being called on a Saturday.
    
    RETURNS
    False: if no failure
    True: if failure'''
    try:
        writeattendance(attendees)
        return False

    except KeyError:
        return True


async def attendanceWrapper(ctx):
    '''This wrapper exists so that attendance can be called outside of doAttendance
    as doAttendance is a command object'''
    attendees=await getAttendance(ctx)

    failure=callAttendance(attendees)

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
    '''Records current attendees in the sheet.'''

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
async def giveAdvice(ctx):
    '''Gives you advice based on your roles
    If you're a scout you will get mostly useful advice'''
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
                            await ctx.send("You will get serious advice as you are new here:")
                            await ctx.send(random.choice(mainRoleResponses[role]))
                            continue

                        #1/2 chance to say something per role so that less messages are sent
                        if random.choice([True, False]):
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
    Arguments: #mention a text channel or 'global' for the whole discord'''

    async def getAllMessages(channels: List[TextChannel])-> Generator[int, int, None]:
        '''Generator for the entire server's messages'''

        for channel in channels:
            count=0
            history=channel.history(limit=5000, after=after)

            while count!=5000:  #ensuring that no more than 5k messages are processed per channel
                try:
                    message=await history.next()
                    count+=1

                except NoMoreItems:
                    break

                except Forbidden:  #ignore channels that the bot can't read
                    continue

            yield count


    print(f"Command: countMessages call recieved. Args = {name}")

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
            history=channel.history(limit=5000, after=after)  #HistoryIterator isn't iterable (╯°□°）╯︵ ┻━┻

            #iterate over messages
            while count!=5000:  #ensuring that no more than 5k messages are processed
                try:
                    await history.next()
                    count+=1

                except NoMoreItems:
                    break

                except Forbidden:  #ignore channels that the bot can't read
                    continue

        else:  #if global check
            async for channelMessageCount in getAllMessages(server.text_channels):
                count+=channelMessageCount
        

        #reacting
        if server is not None:
            if count<=600:
                messageSuffix="A quiet day aboard Erioch"

            elif 600<count<800:
                messageSuffix="A mild hull breach occurred. It's fixed now, My Lord"

            elif 800<count<1000:
                messageSuffix="Maintenance in the engine room occurred today. Many souls were lost"

            elif 1000<count<1200:
                messageSuffix="We were planning to make war"

            else:
                messageSuffix="We suffered an Eldar incursion"

        else:
            if count<=100:
                messageSuffix="Not much happened, My Lord"

            elif count>200:
                messageSuffix="The Guardsmen were arguing again"

            elif 400<count<500:
                messageSuffix="A minor brawl. Nothing too serious, My Lord"

            else:  #if more than 300
                messageSuffix="Chaos cultists were uprooted from their despicable congregation"

        if server is None:
            return await ctx.send(f"Status report, Sir: {count} messages were sent today in {channel.mention}. {messageSuffix}")

        else:  #global is True
            return await ctx.send(f"Status report, Sir: {count} messages were sent today in our glorious vessel. {messageSuffix}")


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
        if difference<0.1:
            suffixString="I came as fast as I could"

        elif 0.1<=difference<0.5:
            suffixString="I polished your armour"

        else:
            suffixString="The Tyranids are coming! You must escape now and send word to Terra"

        print(f"Command: ping call recieved.\n   Process time: {difference} seconds\n   Latency: {bot.latency}")
        return await ctx.send(f"Latency: {bot.latency:.2f}\nI took {difference:.2f} seconds to get here. {suffixString}")



def main():
    '''Put all function calls in here.
    This function will add the function calls to the event loop
    to execute them.
    Please avoid long periods of blocking
    or the bot will run like shit.
    Also runs extra threads'''

    commandListener(bot)
    bot.run(token)
    

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
    botOverride.getChannels()

    #set status
    status=Activity(name="Purging Heretics and Patting Lolis", type=ActivityType.playing)
    await bot.change_presence(activity=status)

    #scheduling the attendance function
    timenow=D.datetime.now()
    if timenow.weekday() == 5:  #no events on Saturday
        return

    timenow=timenow.time()

    if 2000<int(timenow.strftime("%H%M"))<2200:  #if started during an event
        attendees=await executeOnEvents(AsyncCommand(getAttendance, name="getAttendance", arguments=(bot.get_guild(545422040644190220),)))
        failure=callAttendance(attendees)

        if failure:
            await botChannel.send('We do not take roll call on Saturdays!')

    else:  #wait until almost event time
        target=D.time(19, 59)
    
        newTarget=D.datetime.combine(D.date.min, target)
        oldTime=D.datetime.combine(D.date.min, timenow)
        runInSeconds= (newTarget - oldTime).seconds

        await asyncio.sleep(runInSeconds)

        await getInOpsInner()  #ping people to get in ops

        attendees=await executeOnEvents(AsyncCommand(getAttendance, name="getAttendance", arguments=(bot.get_guild(545422040644190220),)))
        failure=callAttendance(attendees)

        if failure:
            await botChannel.send('We do not take roll call on Saturdays!')

if __name__=="__main__":
    main()
    