#author: stalkopat
from __future__ import print_function
import pickle
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
#id can be found from the URL of the sheet
with open('Text Files/sheetID.txt') as f:
    line=f.readline()
    SPREADSHEET_ID = line.strip('\n')

#SPREADSHEET_ID = '1FyxzFPl0qWJOHQGlp3h_CumSyDyQN0VuBbldS1n3PIY'
RANGE = 'Outfit Activity!A5:B'

#this dict is probably wrong
'''TableRanges = {
    "0": {
        "weekday": "Monday",
        "type" : "Aircraft",
        "column" : "17"
    },"1": {
        "weekday": "Tuesday",
        "type" : "Armour",
        "column" : "12"
    },"2": {
        "weekday": "Wednesday",
        "type" : "Infantry",
        "column" : "7"
    },"3": {
        "weekday": "Thursday",
        "type" : "Join Ops",
        "column" : "27"
    },"4": {
        "weekday": "Friday",
        "type" : "Join Ops",
        "column" : "22"
    },"6": {
        "weekday": "Sunday",
        "type" : "Internal Ops",
        "column" : "2"
    }
}'''

#speculative fix dict
TableRanges = {
    "0": {
        "weekday": "Monday",
        "type" : "Aircraft",
        "column" : "2"
    },"1": {
        "weekday": "Tuesday",
        "type" : "Armour",
        "column" : "7"
    },"2": {
        "weekday": "Wednesday",
        "type" : "Infantry",
        "column" : "12"
    },"3": {
        "weekday": "Thursday",
        "type" : "Join Ops",
        "column" : "17"
    },"4": {
        "weekday": "Friday",
        "type" : "Join Ops",
        "column" : "22"
    },"6": {
        "weekday": "Sunday",
        "type" : "Internal Ops",
        "column" : "27"
    }
}

def getweekday(date):
    return date.weekday()

def columnfromdate(date):
    return int(TableRanges[str(getweekday(date))]['column'])+ int(date.day/7)-1

def currentcolumn():
    return columnfromdate(datetime.datetime.today())

def setgreen(row, column):
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
                #SheetId is a hardcoded property of a sheet, using names is unreliable due to renaming of tables
                "sheetId": 1652292470,
                "startRowIndex": row,
                "endRowIndex": int(row) + 1,
                "startColumnIndex": column,
                "endColumnIndex": int(column) + 1
            }}}

def setred(row, column):
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
                "sheetId": 1652292470,
                "startRowIndex": row,
                "endRowIndex": int(row) + 1,
                "startColumnIndex": column,
                "endColumnIndex": int(column) + 1
            }}}

    


def writeattendance(Names):
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


    service = build('sheets', 'v4', credentials=creds)
    #Sheets API
    sheet = service.spreadsheets()
    sheetvals = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE).execute()
    values = sheetvals.get('values', [])

    #Requestlist for batchupdate (Cell Formatting)
    requestlist = []

    if not values:
        print('No data found.')
    else:
        #Iterate over rows and check attendance
        for id, row in enumerate(values):
            if(row[0] in Names):
                requestlist.append(setgreen(id+4, currentcolumn()))
            else:
                requestlist.append(setred(id+4, currentcolumn()))

        #Create request body and batchUpdate the spreadsheet
        body = {
            'requests': requestlist
        }
        response = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()


def main():
    writeattendance([])

if __name__ == '__main__':
    main()