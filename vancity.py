from __future__ import print_function

from datetime import datetime, timedelta
import substring as substring
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

DRIVE_CREATE_TIME_TEMPLATE = '%Y-%m-%dT%H:%M:%S.%fZ'

printDebug = False
debugTeamName = "LIVERPOOL FC"
pageToken = None
useMaxPointsPerTeam = True
reviewedVideos = dict()
unreviewedVideos = dict()
notFoundPlayerVids = dict()
playerPointsByDay = dict()        # playerName : [7] for the days
playersData = dict()

REVIEWED_KEYWORDS = {'reviewed', 'reviwed', 'reeviewed', 'reveiwed'}
VIDEO_UPLOAD_ROOT_FOLDER = 'TEAMS (UPLOAD VIDS HERE)'
FOLDERS_TO_SKIP = ['Example Summary Video 15s Each Drill.mp4']
DRIVE_FILE_IDS_TO_SKIP = ['1T4AuX_4QB65P-JJE69yDv4_KC7s7DTFQ']
LEVELS = {"juniors", "2010", "2009", "2008", "2007", "2006"}
POINTS = {"juniors": 3, "2010": 3, "2009": 5, "2008": 5, "2007": 10, "2006": 10}

teamPointsByDay = [{"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0, "BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0},
                   {"CHELSEA FC": 0, "FC BARCELONA": 0, "CLUB ATHLETICO DE MADRID": 0, "VALENCIA CF": 0,"BAYERN MUNICH": 0, "TOTTENHAM HOTSPURS": 0, "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0, "MANCHESTER CITY": 0, "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0}]
PLAYERLEVELS = {"TJ Tahid":"2007", "Evan Semple":"2007","Logan MacDonald":"2007","Zachary Zach Uppal":"2007","Anthany De Sousa":"2007","Brody Perkin":"2007","Mohamed Konneh":"2007","Tristan Otuomagie":"2007","Connor Ho":"2007","Jacob Haile":"2007","Matthew Robinson":"2007",
                "Koben Armer-Petrie":"2008","Manav Tatla":"2007","Tony Balaj-Coroiu":"2007","Anthony Balaj-Coroiu":"2007","Jakob Grummisch":"2007","Trey Uppal":"2007","Shaan Uppal":"2008","Liam Ferdinandez":"2007","Joaquim Dharamsi":"2007","Alex Boardman":"2007","Francesco":"2007","Pedro":"2007",
                "Brady Verge":"2008","Musa Konneh":"2008","Kaleb Otuomagie":"2008","Kristian Miletic":"2008","Aidan Best":"2008","William Segal":"2008","Alessandro Sandro Troisi":"2008","Ben MacKinnon":"2008",
                "Gurmeet Singh":"2009","Ben Blake":"2009","Lucas Clark":"2009","Mohamed Dolley":"2009","Jonas Caligiuri":"2009","Luca Pedrosa":"2009","Prabhjot Brar":"2009","Jamil Tahid":"2009","Vitor Conradt":"2009","Jonah Haile":"2009","Matteo C":"2009","Zayda":"2009","Jackson":"2009","Aiden":"2009","Jake McAdam":"2009",
                "Louie Bellini":"2009","Luke McKie":"2009","Oliver Schlesinger":"2009","Holly Davis":"2009","Diyae Rafi":"2009","Martin Prochazka":"2009","Nahuel Santamaria":"2009","Kai Tiearney":"2007","Alistair Warren":"2009","Matthew Cornell":"2009","Matty":"2009","Stefano ":"2009","Jericho Carlos":"2009",
                "Carter Jansen":"2010","Jared Hare":"2010","Goodluck ":"2010","Logan Black":"2010","Logan B.":"2010","Andrew Cornell":"2010","Kiyan Malik":"2010","Matteo Troisi":"2010","Teagan Sinclair":"2010","Ryan":"2010",
                "Noah Bellini":"juniors","Cesare Caligiuri":"juniors","Maxim Dharamsi":"juniors","Louis Tiearney":"juniors","Leo Tiearney":"juniors","Abdulai Dolley":"juniors","Alex Balaj-Coroiu":"juniors","Alexander Balaj-Coroiu":"juniors","Daniel Bzowski":"juniors","Emerson Krishna":"juniors","Inti Santamaria":"juniors","Johnson Kengni":"juniors","Abdulai":"juniors","Avery":"juniors"}
TEAMPLAYERS = { "ARSENAL FC":["Goodluck", "Joaquim","Kai", "Ryan"],
                "ATALANTA BC":["Mohamed Konneh","Koben","Carter"],
                "BAYERN MUNICH":["Jacob","Kaleb","Luca P","Johnson"],
                "BORUSSIA DORTMUND":["Anthony","Jake McAdam","Ben Blake","Alexander Balaj-Coroiu"],
                "CHELSEA FC":["Trey","Jackson","Martin","Avery"],
                "CLUB ATHLETICO DE MADRID":["Matthew Robinson","Ben MacKinnon","Jamil","Matthew Cornell"],
                "FC BARCELONA":["Cesare", "Jonas", "Matthew Cornell", "Kenny Amankwa"],
                "JUVENTUS":["Gurmeet","Louie Bellini","Abdulai"],
                "LIVERPOOL FC":["Zachary","Kiyan","Noah Bellini"],
                "MANCHESTER CITY":["Manav","Matteo Caligiuri","Emerson","Jericho"],
                "OLYMPIQUE LYONNAIS":["Tristan","Musa","Alistair","Maxim"],
                "PARIS ST-GERMAIN":["TJ","Vitor","Louis Tiearney"],
                "REAL MADRID CF":["Liam","Pedro","Zayda"],
                "SSC NAPOLI":["Alex Boardman","Shaan","Holly","Logan Black"],
                "TOTTENHAM HOTSPURS":["Logan MacDonald","Jonah","Mohamed Dolley","Andrew Cornell"],
                "VALENCIA CF":["Evan","Brady","Lucas","Daniel"]}


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
        videoFileName = videofile.get('name')
        videoCreatedTime = videofile.get('createdTime')

        createdTimeZ = datetime.strptime(videoCreatedTime, DRIVE_CREATE_TIME_TEMPLATE)
        createdTime = createdTimeZ - timedelta(hours=8)
        #
        # slashIndex = videoFileName.find("/")
        # if slashIndex != -1:
        #     fileNameDay = substring.substringByInd(videoFileName, slashIndex + 1, slashIndex + 2, 1)
        #     if fileNameDay[0] == '0':
        #         fileNameDay = substring.substringByInd(videoFileName, slashIndex + 2, slashIndex + 2, 1)
        #
        #     try:
        #         delta = createdTime.day - int(fileNameDay)
        #         if delta > 0:
        #             createdTime = createdTime - timedelta(days=delta)
        #     except:
        #         print("Failed on vid name parsing to adjust createdTime videoName={} created={} fileNameDay={}".format(videoFileName, createdTime, fileNameDay))

        vidName = getStrippedVideoName(videoFileName)
        if any(text in vidName for text in REVIEWED_KEYWORDS):
            # handle dupes
            if videoFileName in reviewedVideos:
                if printDebug: print("Duplicate Video Found in Reviewed={}".format(videoFileName))
                continue
            reviewedVideos[videoFileName] = [teamName, createdTime]
        else:
            # handle dupes
            if videoFileName in unreviewedVideos:
                if printDebug: print("Duplicate Video Found in unreviewedVideos={}".format(videoFileName))
                continue
            unreviewedVideos[videoFileName] = [teamName, createdTime]

        # if printDebug: print('\tFound file: %s (%s)' % (videoFileName, videoFileid))


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
def determinePlayerPoints(videoName, playerName, teamName):
    if useMaxPointsPerTeam:
        team = TEAMPLAYERS[teamName]

        points = 0
        if len(team) == 3:
            points = 16
        elif len(team) == 4:
            points = 12

        if points == 0:
            print("team {} has {} players".format(teamName, len(team)))
            exit()

        return points

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
    global teamPointsByDay
    global playerPointsByDay
    global debugTeamName
    global playersData

    dayIndex = 0
    if teamName == debugTeamName:
        dayIndex = 1

    # Check the video against all the players in this team
    for playerName in teamPlayerList:
        # for the video player combination, if this video belongs to the player
        # then they should get points
        points = determinePlayerPoints(videoName, playerName, teamName)
        if points is None:
            continue

        # at this point we should have a video with a player in it and so assign the points
        # mon = 1 and sunday = 7
        dayIndex = videoCreatedOn.isoweekday()

        # Did we already account for this player?  (i.e more than one video uploaded)
        playerDays = playerPointsByDay[playerName]
        if playerDays[dayIndex] != 0:
            if teamName == debugTeamName:
                print("(Already Awarded) player=[{} points={} video={}".format(playerName, points, videoName))
            return points

        currentPoints = teamPointsByDay[dayIndex][teamName]
        newPoints = currentPoints + points
        teamPointsByDay[dayIndex][teamName] = newPoints
        playerDays[dayIndex] = newPoints
        playerPointsByDay[playerName] = playerDays
        playersData[videoName] = dict({teamName:{playerName: points}})
        if teamName == debugTeamName:
            print("(First Award) player={} points=[{}] video={}".format(playerName, points, videoName))
        return points

    return None


# -------------------------------------------------------------------------------------------------
def calculatePointSummary():
    global notFoundPlayerVids
    global playerPointsByDay
    global playersData

    print()
    # reviewedVideos is reviewedVideos[videoFileName] = [teamFolderName, videoCreatedTime]
    for videoName in reviewedVideos:
        teamName = reviewedVideos[videoName][0]
        videoCreatedOn = reviewedVideos[videoName][1]

        if teamName in TEAMPLAYERS:
            teamPlayerList = TEAMPLAYERS[teamName]
        else:
            print("Failed to get player list for team {}".format(teamName))
            continue

        for player in teamPlayerList:
            days = [0] * 8
            if player in playerPointsByDay:
                continue
            playerPointsByDay[player] = days

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
    print("Total Videos: {}".format(reviewedVideos.__len__() + unreviewedVideos.__len__()))
    print("reviewedVideos: {}".format(reviewedVideos.__len__()))
    print("Not Reviewed: {}".format(unreviewedVideos.__len__()))


# -------------------------------------------------------------------------------------------------
def printNotReviewedSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("VIDEOS PENDING REVIEW")
    print('----------------------------------------------------------------------------------------')
    longestLen = 0
    for videoName in unreviewedVideos:
        length = unreviewedVideos[videoName][0].__len__()
        if length > longestLen:
            longestLen = length

    for videoName in unreviewedVideos:
        teamName = unreviewedVideos[videoName][0]
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
    global teamPointsByDay
    DAYNAMES = [None, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for dayIndex in range(1, 7):    # Monday (1) to Sunday (7)
        print("{} as {}".format(DAYNAMES[dayIndex], dayIndex))

        dayPointsList = teamPointsByDay[dayIndex]
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
              "TOTTENHAM HOTSPURS": 0,
              "ATALANTA BC": 0, "PARIS ST-GERMAIN": 0, "OLYMPIQUE LYONNAIS": 0, "LIVERPOOL FC": 0, "SSC NAPOLI": 0,
              "MANCHESTER CITY": 0,
              "ARSENAL FC": 0, "REAL MADRID CF": 0, "JUVENTUS": 0, "BORUSSIA DORTMUND": 0}
    for dayIndex in range(1, 7):  # Monday (1) to Sunday (7)
        dayPointsList = teamPointsByDay[dayIndex]
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
    for video in reviewedVideos:
        teamName = reviewedVideos[video][0]
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

            # if printDebug: print('Found team folder: {} ({})'.format(teamFolderName, teamFolderId))

            # populate the reviewedVideos and unreviewedVideos lists
            getTeamVideoInfo(DRIVE, teamFolderId, teamFolderName)

        if pageToken is None:
            break

    calculatePointSummary()

    printNotReviewedSummary()
    printDataSummary()
    # if printDebug: printTeamDailyPointSummary()
    printTeamPointsForWeekSummary()
    printFailedSummary()
    print()
    print("End")


# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
