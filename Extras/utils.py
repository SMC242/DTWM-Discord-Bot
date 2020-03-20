"""Utility functions."""

import re
from typing import *
from discord import *
from classes import AsyncCommand

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


def validateString(string: str, validAnswers: List[str]=None)-> bool:
    '''Check if the input is valid against basic checks and validAnswers, if not None
    
    CHECKS
    length is not 0
    string is not empty
    string is in validAnswers if exists
    
    string: the input to be validated
    validAsnwers: string must be in this list to be valid
    
    RETURNS
    True: if valid
    False: if not valid'''

    if string == "":
        return False

    elif len(string) == 0:
        return False

    elif validAnswers is not None and string not in validAnswers:
        return None

    else:
        return True


def createListFromFile(filePath, type=str):
    '''Returns a list populated by parsed lines from a text file.
    Prefixes filePath with 'TextFiles/'.

    filePath: string path of the file to be read
    varList: output list
    type: the type of variables to be read (str, int, float, etc)'''

    with open("Text Files/"+filePath) as f:
       varList=[type((line.strip("\n")).lower()) for line in f]
    
    return varList  


def insertionSort(unsorted: list)->list:
    '''Sorts the input list and returns a sorted list
    
    Adapted from https://www.geeksforgeeks.org/python-program-for-insertion-sort/'''

    for outerCount in range(1, len(unsorted)-1):
        current=unsorted[outerCount]
        innerCount=outerCount-1

        while innerCount>=0 and current < unsorted[innerCount]:
            unsorted[innerCount+1]=unsorted[innerCount]
            innerCount-=1

            unsorted[innerCount+1]=current

    return unsorted


def binarySearch(target, toSearch: list, returnIndex=True)->Union[int, bool]:
    '''Search the input list for target

    returnIndex: true=return index of target. False=return found bool'''

    lower=0
    upper=len(toSearch)-1
    mid=lower + ((upper-lower) // 2)
    found=False

    while not found and lower<=upper:
        mid=lower + ((upper-lower) // 2)

        if toSearch[mid]==target:  #target is found
            found=True

        elif toSearch[mid]>target:  #target is smaller than current
            upper=mid-1

        else:  #target is larger than current
            lower=mid+1

    if found:
        if returnIndex:
            return mid

        else:
            return True

    else:
        return False


def searchWord(word: str, msg: Union[Message, str])->bool:
    '''Returns a bool based on whether the word is in the message'''

    #ensuring msg is a string
    if isinstance(msg, Message):
        msg=msg.contents

    return (re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(msg)) is not None