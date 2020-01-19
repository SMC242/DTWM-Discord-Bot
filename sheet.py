#author: stalkopat
from __future__ import print_function
import pickle, os.path, datetime, asyncio
from async_property import async_property
from typing import *
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class SheetHandler:
    '''Handles writing to the sheet'''

    #attributes
    # If modifying these scopes, delete the file token.pickle.
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    range = 'Outfit Activity!A5:B'

    tableRanges = {
        0: {
            "weekday": "Monday",
            "type" : "Aircraft",
            "column" : 2
        },
        1: {
            "weekday": "Tuesday",
            "type" : "Armour",
            "column" : 7
        },
        2: {
            "weekday": "Wednesday",
            "type" : "Infantry",
            "column" : 12
        },
        3: {
            "weekday": "Thursday",
            "type" : "Join Ops",
            "column" : 17
        },
        4: {
            "weekday": "Friday",
            "type" : "Join Ops",
            "column" : 22
        },
        6: {
            "weekday": "Sunday",
            "type" : "Internal Ops",
            "column" : 27
        }
    }


    def __init__(self):
        loop = asyncio.get_event_loop()

        #list of coroutines
        tasks=[
            self.getSheet(),
            self.authenticate(),
        ]

        for task in tasks:
            loop.create_task(task)


    async def getSheet(self):
        '''Set the ID and range of the spreadsheet.'''

        with open('Text Files/sheetID.txt') as f:
            self.spreadsheet_ID = f.readline().strip('\n')  #found from the URL of the sheet file

            self.sheet_ID = f.readline().strip("\n")  #found from the GID of the sheet file


    async def authenticate(self):
        #Authentication flow for sheets api
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'Text Files/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)


    async def currentColumn(self, currentDay: int = None, currentDate : datetime.datetime = None):
        '''Get the column for today

        optional: currentDay and currentDate
        '''

        async def today():
            '''Fetches the current day and date
            
            Make a function for performance'''

            currentDate = datetime.datetime.today()

            currentDay = currentDate.weekday()

            return (currentDay, currentDate)
    
        if currentDay is None and currentDate is None:
            currentDay, currentDate = await today()

        return int(self.tableRanges[currentDay]['column']) + int(currentDate.day//7)-1


    def getJSON(self, row: int, column: int, colour: Tuple[int, int, int, int]):
        '''Gets the JSON to set the cell at(row, column) to colour

        colour: the RGBA code for the target colour
            red = (1, 0, 0, 1)
            green = (0, 1, 0, 1)
            black = (0, 0, 0, 1)
        '''

        return {
                "updateCells": {
                "rows": [
                    {
                        "values": [{
                                       "userEnteredFormat": {
                                           "backgroundColor": {
                                               "red": colour[0],
                                               "green": colour[1],
                                               "blue": colour[2],
                                               "alpha": colour[3]
                                           }
                                        }
                                    }
                        ]
                    }
                ],
                "fields": 'userEnteredFormat.backgroundColor',
                "range": {
                    "sheetId": self.sheet_ID,
                    "startRowIndex": row,
                    "endRowIndex": int(row) + 1,
                    "startColumnIndex": column,
                    "endColumnIndex": int(column) + 1
                }
            }
        }


    @async_property
    async def values(self):
        '''Get sheet's values'''

        #Sheets API
        sheet = self.service.spreadsheets()
        sheetvals = sheet.values().get(spreadsheetId = self.spreadsheet_ID,
                                    range = self.range).execute()

        return sheetvals.get('values', [])


    async def writeAttendance(self, Names):
        #Sheets API
        values = await self.values

        #Requestlist for batchupdate (Cell Formatting)
        requestlist = []

        #Iterate over rows and check attendance
        targetColumn = await self.currentColumn()

        for id, row in enumerate(values):
            if(row[0] in Names):
                requestlist.append(self.getJSON(id+4, targetColumn, (0, 1, 0, 1)))
                
            else:
                requestlist.append(self.getJSON(id+4, targetColumn, (1, 0, 0, 1)))

        #Create request body and batchUpdate the spreadsheet
        body = {
            'requests': requestlist
        }

        response = self.service.spreadsheets().batchUpdate(spreadsheetId = self.spreadsheet_ID, body= body).execute()

    async def markAsBlackOnSheet(self, name: str, days: int):
        '''Marks the target player as away on the attendance sheet'''

        values = await self.values
        currentCol = await self.currentColumn()
        
        # binary search for name
        targetRow = None
        for id, row in enumerate(values):
            if row[0] == name:
                targetRow = id + 4 
                break

        if targetRow is None:
            raise ValueError('Target not in sheet')

        # linear search for next boundary
        ranges = list(self.tableRanges.values())
        nextBoundaryIndex = None

        for i, day in enumerate(ranges):
            current = day["column"]
            if current >= currentCol:
                nextBoundaryIndex = i -1  #start at current boundary
                break

        if nextBoundaryIndex is None:  #Sunday
            nextBoundaryIndex = len(ranges) -1

        requestList = []
        currentDate = datetime.datetime.today()
        daysHit = 0  #counter to check for week overflow

        for i in range(0, days):
            #there is no Saturday event
            if nextBoundaryIndex == 5:
                nextBoundaryIndex += 1

            column = await self.currentColumn(nextBoundaryIndex, currentDate)
            
            #check for month overflow
            if column >= 32:
                return

            json = self.getJSON(targetRow, column, (0, 0, 0, 1))
            requestList.append(json)

            #prevent overflow
            if nextBoundaryIndex >= 6:
                nextBoundaryIndex = 0
                currentDate = currentDate + datetime.timedelta(weeks = 1)

            else:
                nextBoundaryIndex += 1

            daysHit += 1
            
        #Create request body and batchUpdate the spreadsheet
        body = {
            'requests': requestList
        }

        response = self.service.spreadsheets().batchUpdate(spreadsheetId = self.spreadsheet_ID, body = body).execute()


def setgreen(row, column):
    '''Deprecated. Use setColour'''

    return {
            "updateCells": {
            "rows": [
                {
                    "values": [{
                                   "userEnteredFormat": {
                                       "backgroundColor": {
                                           "red": 0,
                                           "green": 1,
                                           "blue": 0,
                                           "alpha": 1
                                       }}}
                    ]
                }
            ],
            "fields": 'userEnteredFormat.backgroundColor',
            "range": {
                "sheetId": SHEET_ID,
                "startRowIndex": row,
                "endRowIndex": int(row) + 1,
                "startColumnIndex": column,
                "endColumnIndex": int(column) + 1
            }}}

def setred(row, column):
    '''Deprecated. Use setColour'''

    return {
            "updateCells": {
            "rows": [
                {
                    "values": [{
                                   "userEnteredFormat": {
                                       "backgroundColor": {
                                           "red": 1,
                                           "green": 0,
                                           "blue": 0,
                                           "alpha": 1
                                       }}}
                    ]
                }
            ],
            "fields": 'userEnteredFormat.backgroundColor',
            "range": {
                #SheetId is a hardcoded property of a sheet, using names is unreliable due to renaming of tables
                "sheetId": SHEET_ID,
                "startRowIndex": row,
                "endRowIndex": int(row) + 1,
                "startColumnIndex": column,
                "endColumnIndex": int(column) + 1
            }}}


def main():
    sh= SheetHandler()
    loop = asyncio.get_event_loop()
    task=loop.create_task(sh.writeAttendance(("benmitchellmtbV5",)))
    loop.run_until_complete(task)

    task=loop.create_task(sh.markAsBlackOnSheet("benmitchellmtbV5", 14))
    loop.run_until_complete(task)

if __name__ == '__main__':
    main()