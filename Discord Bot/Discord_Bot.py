from discord import *
from discord.ext import commands
import threading, time, random, asyncio
import datetime as D

from classes import *

bot=commands.Bot(command_prefix="ab!")
token=createListFromFile("token.txt")

startTime=timenow=int(D.datetime.now().strftime("%H%M"))
opsEndTime=startTime+1
print(startTime, " ", opsEndTime)

async def executeOnEvents(func, *args):
    '''Infinitely checks if the time now is during
   the event hours then executes the function if that's true.
   Uses UTC time.
    func: the string name of the function to be executed'''

    varList=[]

    while True:
        timenow=int(D.datetime.now().strftime("%H%M"))

        milestones = createListFromFile("milestones.txt", type=int)
       
        for milestone in milestones:

            if milestone == timenow or int(milestone)-1 == timenow\
               or int(milestone)+1 == timenow or timenow==startTime:
                print(True)

                output=func(*args)

                for element in output:

                    if attendee not in varList:
                        varList.append(element)

                await asyncio.sleep(35)

            else:
                print(False)
                await asyncio.sleep(35)

            if timenow == opsEndTime:
                return varList
            

async def getAttendance():
    '''Returns a list of people in the ops/training channels'''
    #reads the channels to check from a file
    #appends the channel IDs to channels
    channels=createListFromFile("channels.txt")
    delimiters=createListFromFile("delimiters.txt")

    #for every channel in channels it gets the members
    #sequentially and appends them to the list
    channelMembers=[]

    channelMembers=[member.display_name for channel in channels\
        for member in (await bot.fetch_channel(channel)).members]

    #parsing the names
    attendees=[]
    for attendee in channelMembers:
        for delimiter in delimiters:
            try:
                attendee, null=attendee.split(delimiter)
            except ValueError:
                pass

        attendees.append(attendee)

    return attendees

async def attendanceWrapper():
    '''This wrapper exists so that attendance can be called outside of doAttendance
    as doAttendance is a command object'''
    attendees=await getAttendance()
    print(attendees)
    return attendees

@bot.command()
@commands.cooldown(1, 60, type=commands.BucketType.user)
async def doAttendance(ctx):
    '''Work in progress.
    Gets a list of people in the War Room and Training Deck.
    Will send the list ot the attendance sheet soon.'''

    await ctx.send("It will be done, my Lord")

    async with ctx.typing():
        attendees=await attendanceWrapper()

        await ctx.send(f"Attendees: {attendees}")

        await ctx.send("Attendance completed **UmU**")

@bot.command()
@commands.cooldown(1, 2, type=commands.BucketType.user)
async def giveAdvice(ctx):
    '''Gives you advice based on your roles
    If you're a scout you will get mostly useful advice'''
    mainRoleResponses={
        "watch commander" : ["Learn to split <:splitwatch_marines:618120678708609054>",
                             "Become a dictator",
                             "Make good outfit EZ",
                             "If you don't have 70 KPM you can't be a leader 😤"
                             ],

        "watch leader" : ["Why haven't you split yet?",
                          "Just zerg",
                          "Get more zerglings",
                          "Get a life",
                          "MMO mice are good investments",
                          "Recruit plox"
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
            "You can get access to the meme and not safe for life channel by typing .iam heretic in #545818844036464670",
            "To get promoted, you need to attend all 3 basic trainings and be noticed by >= Keepers as well-integrated into the community",
            "You may seek knowledge in our chapter's #551905489236000794 . Training docs will be pinned"
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

        "primarch, reclaimed" :[
            "Train harder",
            "Do some 1v1s",
            ],

        "primarch" :[
            "You can find all relevant information to our co-ops pinned in #566316662748348447",
            ],

        "heretic" :[
            "HERESY DETECTED! COMMENCE VIRUS BOMBING!",
            "I see you're a man of culture",
            "Post something weird in #545809293841006603"
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

            #check each supported role against the invoker's roles
            for role in mainRoleResponses.keys(): 
                
                #limit the responses to up to 4
                if role in roleNames and responseCount<2: 

                    if role=="scout":
                        await ctx.send("You will get serious advice as you are new here:")
                        await ctx.send(random.choice(mainRoleResponses[role]))
                        continue

                    #1/2 chance to say something per role so that less messages are sent
                    if random.choice([True, False]):
                        await ctx.send(random.choice(mainRoleResponses[role]))

                    #sometimes invokers will get a response for their extra roles. 1/9 chance
                    if random.choice([False, False, False, False,\
                       False, False, False, False, True]): 

                        await ctx.send(random.choice(extraRoleResponses\
                            [random.choice([*extraRoleResponses.keys()])]))

                    responseCount+=1


async def sendAttToSheet(attendees):
    '''Sends the results of getAttendance() to the Google Sheet
    Attendees: list of people who attended'''
    pass

def main():
    '''Put all function calls in here.
    This function will add the function calls to the event loop
    to execute them.
    Please avoid long periods of blocking
    or the bot will run like shit.
    Also runs extra threads'''

    #add the async functions to list 1
    #add the args to the corresponding index of list 2 as a tuple
    #if no args: put None in the args index
    asyncToExecute=[
        bot.run,
        executeOnEvents
               ],
    [
        (token),

     ]

    #same as asyncToExecute but with threading.Threads
    threadsToExecute=[

        ],
    [

        ]

    threads=[threading.main_thread()]

   
    loop=asyncio.get_event_loop()

    

    if len(asyncToExecute) != 0:
        for i in range(0, len(asyncToExecute)-1):
            #Ensuring correct type for the args
           if not isinstance(asyncToExecute[1][i], tuple) or not isinstance(threadsToExecute[1][i])\
           and asyncToExecute[1][i] is not None and threadsToExecute[1][i] is not None:
               raise TypeError("Tuple not passed in main(). Check the arguments lists")

            if asyncToExecute[1][i] is not None:
                
                coroutine=asyncToExecute[0][i](asyncToExecute[1][*i])
            else:
                coroutine=asyncToExecute[0][i]()

            
            
            #sadly our version of asyncio doesn't support the name kwarg
            loop.create_task(coroutine)

        if len(threadsToExecute) != 0:
            #starting the threads
            for i in range(0, len(threadsToExecute)-1):

                if threadsToExecute[1] [i] is not None:
                    threads.insert(0, threading.Thread(target=threadsToExecute[0][i], args=threadsToExecute[1][*i], name=threadsToExecute[0][i].__name__))

                else:
                    threads.insert(0, threading.Thread(target=threadsToExecute[0][i], name=threadsToExecute[0][i].__name__))

            for i in range(1, len(threads)-1):
                thread.start()

    commandListener(loop, threads)

@bot.listen()
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    botChannel=bot.get_channel(545818844036464670)
    await botChannel.send('I have awoken... I am at your service')

    #scheduling the attendance function
    timenow=int(D.datetime.now().strftime("%H%M"))
    runInSeconds = int(opsEndTime)-timenow

    await asyncio.sleep(runInSeconds)

    await executeOnEvents(attendanceWrapper)

main()