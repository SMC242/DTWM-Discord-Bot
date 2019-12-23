#authors: benmitchellmtb, ScreaminSteve, FasterNo1
from discord import *
from discord.ext import commands
import threading, time, random, asyncio
import datetime as D
from typing import *

from classes import *
from sheet import *

bot=commands.Bot(command_prefix="ab!")
bot.add_cog(botOverrides(bot))

with open("Text Files/token.txt") as f:
    line=f.readline()
    token=line.strip("\n")

async def executeOnEvents(func: AsyncCommand):
    '''Infinitely checks if the time now is during
   the event hours then executes the function if that's true.
   Uses UTC time.
    func: the AsyncCommand object to call on each milestone'''
    print(f"Scheduled Event ({func.name}): beginning execution")

    varList=[]

    while True:
        success=False

        timenow=D.datetime.now().strftime("%H%M")

        milestones = createListFromFile("milestones.txt", type=int)
       
        for milestone in milestones:
            milestone=int(milestone)

            if milestone == int(timenow) or milestone-1 == int(timenow)\
               or milestone+1 == int(timenow):
                print(f"Scheduled Event ({func.name}): milestone hit: {timenow}")
                success=True

                output= await func.call()

                for element in output:

                    if element not in varList:
                        varList.append(element)

                await asyncio.sleep(35)                

            if timenow == milestones[3]:
                print(f"Scheduled event ({func.name}): execution finished")
                return varList
        
        if not success:
            await asyncio.sleep(35)

            

async def getAttendance():
    '''Returns a list of people in the ops/training channels'''
    #reads the channels to check from a file
    #appends the channel IDs to channels
    channels=createListFromFile("channels.txt")
    delimiters=createListFromFile("delimiters.txt")

    #for every channel in channels it gets the members
    #sequentially and appends them to the list
    channelMembers=[member.display_name for channel in channels\
        for member in (await bot.fetch_channel(channel)).members]

    #parsing the names
    attendees=[]
    for attendee in channelMembers:
        for delimiter in delimiters:
            try:
                attendee, *null=attendee.split(delimiter)

            except ValueError:  #if delimiter not in attendee
                pass

        attendees.append(attendee)

    return attendees

async def attendanceWrapper():
    '''This wrapper exists so that attendance can be called outside of doAttendance
    as doAttendance is a command object'''
    attendees=await getAttendance()

    writeattendance(attendees)
    return attendees

@bot.command()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def ayaya(ctx):
    '''Tell the bot to be a weeb'''

    print("Command: ayaya call received")

    choice=random.randint(0,5)

    if choice==0:
        await ctx.send("ayaya!")

    elif choice==1:
        await ctx.send("AYAYA!")

    elif choice==2:
        await ctx.send("ayaya ayaya!")

    elif choice==3:
        await ctx.send("AYAYA AYAYA!")

    elif choice==4:
        await ctx.send("ayaya ayaya ayaya!")

    else:
        await ctx.send("AYAYA AYAYA AYAYA!")


@bot.command()
@commands.cooldown(1, 5, type=commands.BucketType.user)
async def commitNotAlive(ctx):
    '''Tell the bot to kill itself'''
    print("Command: commitNotAlive call recieved")

    choice=random.randint(0, 3)
    if choice==0:
        await ctx.send("no u")

    elif choice==1:
        await ctx.send("commit neck rope")

    elif choice==2:
        await ctx.send("die")

    else:
        await ctx.send("kys")
    

    

@bot.command()
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def doAttendance(ctx):
    '''Work in progress.
    Gets a list of people in the War Room and Training Deck.
    Will send the list ot the attendance sheet soon.'''

    print("Command: doAttendance call recieved")
    await ctx.send("It will be done, my Lord")

    async with ctx.typing():
        attendees=await attendanceWrapper()

        if attendees==[]:
            await ctx.send("Nobody is there, My Liege. Our men have become complacent!")

        else:
            await ctx.send(f"Attendees: {attendees}")

        await ctx.send("Attendance check completed **UmU**")



@bot.command()
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


async def sendAttToSheet(attendees):
    '''Sends the results of getAttendance() to the Google Sheet
    Attendees: list of people who attended'''
    

@bot.command()
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def joindtwm(ctx):
    '''Posts the invite link to the discord'''
    print("Command: joindtwm call recieved")
    await ctx.send('Come quickly, brother! We can always use new Astartes. https://joindtwm.net/join')


def main():
    '''Put all function calls in here.
    This function will add the function calls to the event loop
    to execute them.
    Please avoid long periods of blocking
    or the bot will run like shit.
    Also runs extra threads'''

    #list of AsyncCommands to be added to the event loop
    asyncToExecute=[
        AsyncCommand(bot.start, arguments=token, name="start bot")
    ]

    #list of ThreadCommand objects to be started
    threadsToExecute=[

        ]

    threads=[
        threading.main_thread(),
        ]

    loop=asyncio.get_event_loop()

    #starting the async commands
    for command in asyncToExecute:
        coroutine=command.coro

        loop.create_task(coroutine)

    #starting the threads
    for command in threadsToExecute:
        thread=command.call()
        thread.start()

    commandListener(loop, threads)

    loop.run_forever()


@bot.listen()
async def on_ready():
    print('\nLogged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    botChannel=bot.get_channel(545818844036464670)
    await botChannel.send('I have awoken... I am at your service')

    #scheduling the attendance function
    timenow=D.datetime.now()
    timenow=timenow.time()

    target=D.time(19, 59)
    
    newTarget=D.datetime.combine(D.date.min, target)
    oldTime=D.datetime.combine(D.date.min, timenow)
    runInSeconds= (newTarget - oldTime).seconds

    if 2000<int(timenow.strftime("%H%M"))<2200:  #if started during an event
        return await executeOnEvents(AsyncCommand(attendanceWrapper, name="attendanceWrapper"))

    else:
        await asyncio.sleep(runInSeconds)

        return await executeOnEvents(AsyncCommand(attendanceWrapper, name="attendanceWrapper"))

main()