from __future__ import print_function

from datetime import datetime, timedelta

import substring as substring
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

DRIVE_CREATE_TIME_TEMPLATE = '%Y-%m-%dT%H:%M:%S.%fZ'

debugTeamName = ""
pageToken = None
printDebug = False
reviewed = dict()
notReviewed = dict()
notFoundPlayerVids = dict()
playerAwardedForDay = dict()        # playerName : [7] for the days

REVIEWED_KEYWORDS = {'reviewed', 'reviwed', 'reeviewed', 'reveiwed'}
VIDEO_UPLOAD_ROOT_FOLDER = 'TEAMS (UPLOAD VIDS HERE)'
FOLDERS_TO_SKIP = ['Example Summary Video 15s Each Drill.mp4']
DRIVE_FILE_IDS_TO_SKIP = ['1T4AuX_4QB65P-JJE69yDv4_KC7s7DTFQ']
LEVELS = {"juniors", "2010", "2009", "2008", "2007", "2006"}
POINTS = {"juniors": 3, "2010": 3, "2009": 5, "2008": 5, "2007": 10, "2006": 10}

pointsByDay = [{"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
               {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPUR": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0}]
PLAYERLEVELS = {"TJ Tahid":"2007", "Evan Semple":"2007","Logan MacDonald":"2007","Zachary Zach Uppal":"2007","Anthany De Sousa":"2007","Brody Perkin":"2007","Mohamed Konneh":"2007","Tristan Otuomagie":"2007","Connor Ho":"2007","Jacob Haile":"2007","Matthew Robinson":"2007",
                "Koben Armer-Petrie":"2008","Manav Tatla":"2007","Tony Balaj-Coroiu":"2007","Anthony":"2007","Jakob Grummisch":"2007","Trey Uppal":"2008","Shaan Uppal":"2008","Liam Ferdinandez":"2007","Joaquim Dharamsi":"2007","Alex Boardman":"2007","Francesco":"2007","Pedro":"2007",
                "Brady Verge":"2008","Musa Konneh":"2008","Kaleb Otuomagie":"2008","Kristian Miletic":"2008","Aidan Best":"2008","William Segal":"2008","Alessandro Sandro Troisi":"2008","Ben MacKinnon":"2008",
                "Gurmeet Singh":"2009","Ben Blake":"2009","Lucas Clark":"2009","Mohamed Dolley":"2009","Jonas Caligiuri":"2009","Luca Pedrosa":"2009","Prabhjot Brar":"2009","Jamil Tahid":"2009","Vitor Conradt":"2009","Jonah Haile":"2009","Matteo C":"2009","Zayda":"2009","Jackson":"2009","Aiden":"2009","Jake McAdam":"2009",
                "Louie Bellini":"2009","Luke McKie":"2009","Oliver Schlesinger":"2009","Holly Davis":"2009","Diyae Rafi":"2009","Martin Prochazka":"2009","Nahuel Santamaria":"2009","Kai Tiearney":"2009","Alistair Warren":"2009","Matthew Cornell":"2009","Matty":"2009","Stefano ":"2009","Jericho Carlos":"2009",
                "Carter Jansen":"2010","Jared Hare":"2010","Goodluck ":"2010","Logan Black":"2010","Andrew Cornell":"2010","Kiyan Malik":"2010","Matteo Troisi":"2010","Teagan Sinclair":"2010","Ryan":"2010",
                "Noah Bellini":"juniors","Cesare Caligiuri":"juniors","Maxim Dharamsi":"juniors","Louis Tiearney":"juniors","Leo Tiearney":"juniors","Abdulai Dolley":"juniors","Alexander Balaj-Coroiu Alex":"juniors","Daniel Bzowski":"juniors","Emerson Krishna":"juniors","Inti Santamaria":"juniors","Johnson Kengni":"juniors","Abdulai":"juniors","Avery":"juniors"}
TEAMPLAYERS = { "CHELSEA FC":["Anthany","Aiden","Jackson","Martin","Avery"],
                "FC BARCELONA":["Brody","Sandro","Alessandro","Jonas","Matthew Cornell", "Matty", "Cesare"],
                "CLUB ATHLETICO DE MADRID":["Matthew Robinson","Ben MacKinnon","Jamil","Nahuel"],
                "VALENCIA CF":["Evan","Brady","Lucas","Daniel"],
                "BAYERN MUNICH":["Jacob","Kaleb","Luca P","Inti"],
                "TOTTENHAM HOTSPUR":["Logan MacDonald","Jonah","Mohamed Dolley","Andrew","Johnson"],
                "ATALANTA BC":["Mohamed Konneh","Koben","Prabhjot","Carter","Leo"],
                "PARIS ST-GERMAIN":["TJ","Kristian","Vitor","Louis Tiearney"],
                "OLYMPIQUE LYONNAIS":["Tristan","Musa","Alistair","Maxim"],
                "LIVERPOOL FC":["Zach","Zachary","William","Kiyan","Noah Bellini"],
                "SSC NAPOLI":["Alex Boardman","Shaan","Holly","Logan Black","Matteo T"],
                "MANCHESTER CITY":["Jakob","Francesco","Emerson","Jericho"],
                "ARSENAL FC":["Joaquim","Gurmeet","Matteo C","Ryan"],
                "REAL MADRID CF":["Liam","Pedro","Kai","Zayda"],
                "JUVENTUS":["Manav","Trey","Louie Bellini","Abdulai"],
                "BORUSSIA DORTMUND":["Anthony","Jake McAdam","Ben Blake","Luke","Alexander Balaj-Coroiu Alex"]}


# -------------------------------------------------------------------------------------------------
def loadDriveApi():
    SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    return DRIVE


# -------------------------------------------------------------------------------------------------
def getDriveFolderContents(drive, folderId):
    global pageToken
    return drive.files().list(q="'{}' in parents".format(folderId),
                              spaces='drive',
                              fields='nextPageToken, files(id, name, createdTime)',
                              pageToken=pageToken).execute().get('files', [])


# -------------------------------------------------------------------------------------------------
def getRootFolderId(drive):
    global pageToken
    response = drive.files().list(q="name contains '{}'".format(VIDEO_UPLOAD_ROOT_FOLDER),
                                  spaces='drive',
                                  fields='nextPageToken, files(id, name)',
                                  pageToken=pageToken).execute()
    pageToken = response.get('nextPageToken', None)
    rootFolderList = response.get('files', [])
    if rootFolderList.__len__() > 1:
        print("Failure: Too many root folders: found {}".format(rootFolderList))
        exit(2)

    rootFolder = rootFolderList[0]
    return rootFolder.get('id')


# -------------------------------------------------------------------------------------------------
def getTeamVideoInfo(drive, teamFolderId, teamName):
    teamvids = getDriveFolderContents(drive, teamFolderId)
    for videofile in teamvids:
        videoFileid = videofile.get('id')
        videoFileName = videofile.get('name')
        videoCreatedTime = videofile.get('createdTime')

        createdTimeZ = datetime.strptime(videoCreatedTime, DRIVE_CREATE_TIME_TEMPLATE)
        createdTime = createdTimeZ - timedelta(hours=8)

        slashIndex = videoFileName.find("/")
        if 0 < slashIndex <= 3:
            fileNameDay = substring.substringByInd(videoFileName, slashIndex + 1, slashIndex + 2, 1)
            if fileNameDay[0] == '0':
                fileNameDay = substring.substringByInd(videoFileName, slashIndex + 2, slashIndex + 2, 1)

            try:
                delta = createdTime.day - int(fileNameDay)
                if delta > 0:
                    createdTime = createdTime - timedelta(days=delta)
            except:
                print("Failed on vid name parsing to adjust createdTime videoName={} created={} fileNameDay={}".format(videoFileName, createdTime, fileNameDay))

        vidName = getStrippedVideoName(videoFileName)
        if any(text in vidName for text in REVIEWED_KEYWORDS):
            # handle dupes
            if videoFileName in reviewed:
                if printDebug: print("Duplicate Video Found in Reviewed={}".format(videoFileName))
                continue
            reviewed[videoFileName] = [teamName, createdTime]
        else:
            # handle dupes
            if videoFileName in notReviewed:
                if printDebug: print("Duplicate Video Found in notReviewed={}".format(videoFileName))
                continue
            notReviewed[videoFileName] = [teamName, createdTime]

        if printDebug: print('\tFound file: %s (%s)' % (videoFileName, videoFileid))


# -------------------------------------------------------------------------------------------------
def getPlayerLevelByName(playerFirstName):
    for entry in PLAYERLEVELS:
        if playerFirstName.lower() in entry.lower():
            return PLAYERLEVELS[entry]

    return None


# -------------------------------------------------------------------------------------------------
def getStrippedVideoName(vidName: str):
    name = vidName
    for c in ['-','_','(',')','[',']','.']:
        name = name.replace(c, " ")
    return name.lower()


# -------------------------------------------------------------------------------------------------
def determinePlayerPoints(videoName, playerName):
    name = playerName
    fixedVidName = getStrippedVideoName(videoName)
    if name is not '' and name.lower() in fixedVidName:
        level = getPlayerLevelByName(name)
        if level is not None:
            points = POINTS[level]
            return points

    if " " not in playerName:
        return None

    nameOptions = playerName.split(" ")
    for name in nameOptions:
        if name is not '' and name.lower() in fixedVidName:
            level = getPlayerLevelByName(name)
            if level is not None:
                points = POINTS[level]
                return points

    return None


# -------------------------------------------------------------------------------------------------
def updatePoints(videoName, videoCreatedOn, teamName, teamPlayerList):
    global pointsByDay
    global playerAwardedForDay
    global debugTeamName

    if teamName == debugTeamName:
        None

    # Check the video against all the players in this team
    for playerName in teamPlayerList:
        # for the video player combination, if this video belongs to the player
        # then they should get points
        points = determinePlayerPoints(videoName, playerName)
        if points is None:
            continue

        # at this point we should have a video with a player in it and so assign the points
        # mon = 1 and sunday = 7
        dayIndex = videoCreatedOn.isoweekday()

        # Did we already account for this player?  (i.e more than one video uploaded)
        playerDays = playerAwardedForDay[playerName]
        if playerDays[dayIndex] != 0:
            if teamName == debugTeamName:
                print("(Already Awarded) player=[{} points={} video={}".format(playerName, points, videoName))
            return points

        currentPoints = pointsByDay[dayIndex][teamName]
        newPoints = currentPoints + points
        pointsByDay[dayIndex][teamName] = newPoints
        playerDays[dayIndex] = newPoints
        playerAwardedForDay[playerName] = playerDays
        if teamName == debugTeamName:
            print("(First Award) player={} points=[{}] video={}".format(playerName, points, videoName))
        return points

    return None


# -------------------------------------------------------------------------------------------------
def calculatePointSummary():
    global notFoundPlayerVids
    global playerAwardedForDay

    print()
    # reviewed is reviewed[videoFileName] = [teamFolderName, videoCreatedTime]
    for videoName in reviewed:
        teamName = reviewed[videoName][0]
        videoCreatedOn = reviewed[videoName][1]

        if teamName in TEAMPLAYERS:
            teamPlayerList = TEAMPLAYERS[teamName]
        else:
            print("Failed to get player list for team {}".format(teamName))
            exit(3)

        for player in teamPlayerList:
            days = [0] * 8
            if player in playerAwardedForDay:
                continue
            playerAwardedForDay[player] = days

        points = updatePoints(videoName, videoCreatedOn, teamName, teamPlayerList)
        if points is None:
            print("Failed to match player to video: Team: {} Video name: {} players: {}".format(teamName, videoName, teamPlayerList))
            notFoundPlayerVids[videoName] = teamName


# -------------------------------------------------------------------------------------------------
def printDataSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("PROGRAM STATS SUMMARY")
    print('----------------------------------------------------------------------------------------')
    print("Total Videos: {}".format(reviewed.__len__() + notReviewed.__len__()))
    print("Reviewed: {}".format(reviewed.__len__()))
    print("Not Reviewed: {}".format(notReviewed.__len__()))


# -------------------------------------------------------------------------------------------------
def printNotReviewedSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("VIDEOS PENDING REVIEW")
    print('----------------------------------------------------------------------------------------')
    longestLen = 0
    for videoName in notReviewed:
        length = notReviewed[videoName][0].__len__()
        if length > longestLen:
            longestLen = length

    for videoName in notReviewed:
        teamName = notReviewed[videoName][0]
        spacesCount = longestLen - teamName.__len__() + 2
        print("\t{}:{}{}".format(teamName, " "*spacesCount, videoName))


# -------------------------------------------------------------------------------------------------
def printFailedSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("FAILED PARSING")
    print('----------------------------------------------------------------------------------------')
    for entry in notFoundPlayerVids:
        print("\t{} {}".format(entry, notFoundPlayerVids[entry]))


# -------------------------------------------------------------------------------------------------
def printTeamDailyPointSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("TEAM POINTS BY DAY")
    print('----------------------------------------------------------------------------------------')
    global pointsByDay
    DAYNAMES = [None, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for dayIndex in range(1, 7):    # Monday (1) to Sunday (7)
        print("{} as {}".format(DAYNAMES[dayIndex], dayIndex))

        dayPointsList = pointsByDay[dayIndex]
        reviewedVideoCount = 0
        for team in dayPointsList:
            print("\t{}: {}".format(team, dayPointsList[team]))


# -------------------------------------------------------------------------------------------------
def printTeamPointsForWeekSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("TEAM POINTS FOR WEEK")
    print('----------------------------------------------------------------------------------------')
    results = {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0, "BAYERN MUNICH": 0,
              "TOTTENHAM HOTSPUR": 0,
              "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0,
              "MANCHESTER CITY": 0,
              "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0}
    for dayIndex in range(1, 7):  # Monday (1) to Sunday (7)
        dayPointsList = pointsByDay[dayIndex]
        for team in dayPointsList:
            currentPoints = results[team]
            newPoints = dayPointsList[team]
            results[team] = currentPoints + newPoints

    for team in results:
        print("\t{}: {}".format(team, results[team]))


# -------------------------------------------------------------------------------------------------
def printVideoCountPerTeam():
    return
    print()
    print('----------------------------------------------------------------------------------------')
    print("VIDEO COUNT PER TEAM")
    print('----------------------------------------------------------------------------------------')
    s = dict()
    for video in reviewed:
        teamName = reviewed[video][0]
        if teamName in s:
            s[teamName] = s[teamName] + 1
        else:
            s[teamName] = 0

    for entry in s:
        print('{} {}'.format(entry, s[entry]))


# -------------------------------------------------------------------------------------------------
def main():
    global pageToken
    DRIVE = loadDriveApi()

    while True:
        print("--------------------------------------------------------")
        print("Getting Drive Data")
        print("--------------------------------------------------------")
        uploadVidsFolderId = getRootFolderId(DRIVE)

        # Get all the data per team folder
        folders = getDriveFolderContents(DRIVE, uploadVidsFolderId)
        for folder in folders:
            teamFolderId = folder.get('id')
            teamFolderName = folder.get('name')

            if teamFolderName in FOLDERS_TO_SKIP or teamFolderId in DRIVE_FILE_IDS_TO_SKIP:
                continue

            if printDebug: print('Found team folder: {} ({})'.format(teamFolderName, teamFolderId))

            # populate the reviewed and notReviewed lists
            getTeamVideoInfo(DRIVE, teamFolderId, teamFolderName)

        if pageToken is None:
            break

    calculatePointSummary()

    printNotReviewedSummary()
    printDataSummary()
    if printDebug: printTeamDailyPointSummary()
    printTeamPointsForWeekSummary()
    printFailedSummary()
    print()
    print("End")


# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
