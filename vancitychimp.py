import datetime
import copy

from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

from report import createReport

pageToken = None

WEEK_1_START_DATE = '2020-03-30'
REVIEWED_KEYWORDS = {'reviewed', 'reviwed', 'reeviewed', 'reveiwed'}
VIDEO_UPLOAD_ROOT_FOLDER = 'TEAMS (UPLOAD VIDS HERE)'
DAYS_OF_THE_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
TEAM_POINTS_TEMPLATE = {"ARSENAL FC": 0, "ATALANTA BC": 0, "BAYERN MUNICH": 0, "BORUSSIA DORTMUND": 0, "CHELSEA FC": 0, "CLUB ATHLETICO DE MADRID": 0, "FC BARCELONA": 0,  "JUVENTUS": 0, "LIVERPOOL FC": 0, "MANCHESTER CITY": 0, "OLYMPIQUE LYONNAIS": 0, "PARIS ST-GERMAIN": 0, "REAL MADRID CF": 0, "SSC NAPOLI": 0, "TOTTENHAM HOTSPURS": 0, "VALENCIA CF": 0}
DAILY_TEAM_POINTS = dict()
for day in DAYS_OF_THE_WEEK:
    DAILY_TEAM_POINTS[day] = copy.deepcopy(TEAM_POINTS_TEMPLATE)
TEAMPLAYERS = {"ARSENAL FC":["Goodluck", "Joaquim","Kai"],
               "ATALANTA BC":["Mohamed Konneh","Koben","Carter","Brody"],
               "BAYERN MUNICH":["Jacob","Kaleb","Luca","Johnson"],
               "BORUSSIA DORTMUND":["Anthony","Jake McAdam","Ben Blake","Alexander Balaj-Coroiu"],
               "CHELSEA FC":["Trey","Jackson","Martin","Avery"],
               "CLUB ATHLETICO DE MADRID":["Matthew Robinson","Ben MacKinnon","Jamil","Clinton Edom"],
               "FC BARCELONA":["Cesare", "Jonas", "Matthew Cornell", "Kenny Amankwa"],
               "JUVENTUS":["Gurmeet","Louie Bellini","Abdulai"],
               "LIVERPOOL FC":["Zachary","Kiyan","Noah Bellini"],
               "MANCHESTER CITY":["Manav","Matteo Caligiuri","Emerson","Jericho"],
               "OLYMPIQUE LYONNAIS":["Tristan","Musa","Alistair","Maxim"],
               "PARIS ST-GERMAIN":["TJ","Vitor","Louis"],
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
    drive = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    return drive


# -------------------------------------------------------------------------------------------------
def getDriveFolderContents(drive, folderId, foldersOnly=True):
    global pageToken

    query = "'{}' in parents and mimeType = 'application/vnd.google-apps.folder'" if foldersOnly else "'{}' in parents and mimeType != 'application/vnd.google-apps.folder'"
    query = query.format(folderId)
    return drive.files().list(q=query,
                              spaces='drive',
                              fields='nextPageToken, files(id, name, createdTime, owners)',
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
def printDataSummary(allVideos):
    reviewedCount = len([vid for vid in allVideos if vid.get('reviewed')])
    print()
    print('----------------------------------------------------------------------------------------')
    print("PROGRAM STATS SUMMARY")
    print('----------------------------------------------------------------------------------------')
    print("Total Videos: {}".format(len(allVideos)))
    print("Totals Reviewed: {}".format(reviewedCount))
    print("Total Unreviewed: {}".format(len(allVideos)-reviewedCount))


# -------------------------------------------------------------------------------------------------
def printNotReviewedSummary(videos):
    print()
    print('----------------------------------------------------------------------------------------')
    print("VIDEOS PENDING REVIEW")
    print('----------------------------------------------------------------------------------------')
    longestLen = 0
    for videoName in videos:
        length = len(videos[videoName])
        if length > longestLen:
            longestLen = length

    for videoName in videos:
        teamName = videos[videoName]
        spacesCount = longestLen - len(teamName) + 2
        print("\t{}:{}{}".format(teamName, " "*spacesCount, videoName))


# -------------------------------------------------------------------------------------------------
def printFailedSummary(videos):
    print()
    print('----------------------------------------------------------------------------------------')
    print("FAILED PARSING")
    print('----------------------------------------------------------------------------------------')
    for entry in videos:
        print("\t{} {}".format(entry, videos[entry]))


# -------------------------------------------------------------------------------------------------
def printTeamPointsForWeekSummary(allVideos):
    print()
    print('----------------------------------------------------------------------------------------')
    print("TEAM POINTS FOR WEEK")
    print('----------------------------------------------------------------------------------------')
    weeklyResults = TEAM_POINTS_TEMPLATE
    for teamsDay in DAILY_TEAM_POINTS:
        for team in DAILY_TEAM_POINTS[teamsDay]:
            weeklyResults[team] += DAILY_TEAM_POINTS[teamsDay][team]

    for team in weeklyResults:
        print("\t{}: {}".format(team, weeklyResults[team]))


# -------------------------------------------------------------------------------------------------
def printSummary(allVideos, failedParsingVideos):
    printDataSummary(allVideos)
    printTeamPointsForWeekSummary(allVideos)
    printFailedSummary(failedParsingVideos)


# -------------------------------------------------------------------------------------------------
def getChimpList(allVideos):
    chimpList = []
    chimpDays = ['monday', 'wednesday', 'friday']
    for video in allVideos:
        day = video.get('day')
        createdTime = video.get('createdTime')
        reviewed = video.get('reviewed')

        datetimeObjCreateTime = datetime.datetime.strptime(createdTime, '%Y-%m-%dT%H:%M:%S.%fZ')  # '2020-05-30T03:41:25.012Z'
        pacificCreateTime = datetimeObjCreateTime - datetime.timedelta(hours=7)
        createdDayOfWeek = DAYS_OF_THE_WEEK[pacificCreateTime.weekday()]

        if day and (day.lower() == createdDayOfWeek.lower()):
            if day in chimpDays:
                if reviewed:
                    chimpList.append(video)

    return chimpList


# -------------------------------------------------------------------------------------------------
def getWeekNumber():
    week1StartDate = datetime.datetime.strptime(WEEK_1_START_DATE, '%Y-%m-%d')  # '2020-05-30'
    now = datetime.datetime.now()
    start = (week1StartDate - datetime.timedelta(days=week1StartDate.weekday()))
    current = (now - datetime.timedelta(days=now.weekday()))
    weekNumber = (current - start).days / 7 + 1
    return int(weekNumber)


# -------------------------------------------------------------------------------------------------
def getSanitizedVideoName(vidName: str):
    name = vidName
    for c in ['-','_','(',')','[',']','.']:
        name = name.replace(c, " ")
    return name.lower()


# -------------------------------------------------------------------------------------------------
def determinePoints(teamName):
    team = TEAMPLAYERS[teamName]
    points = int(48 / len(team))
    if points != int(12) and points != int(16):
        print("math problem with {}".format(teamName))
        exit()

    return points


# -------------------------------------------------------------------------------------------------
def collectVideoDetails(videoDict, teamName):
    videoName = getSanitizedVideoName(videoDict.get('name'))
    createdTime = videoDict.get('createdTime')
    videoDay = getDayFromVideo(videoName)
    player = getPlayerFromVideo(videoName, TEAMPLAYERS[teamName])
    isReviewed = True if any(text in videoName for text in REVIEWED_KEYWORDS) else False
    owners = videoDict.get('owners')
    ownerEmailList = [owner.get('emailAddress') for owner in owners]

    videoDetails = {'name': videoName, 'id': videoDict.get('id'), 'player': player, 'team': teamName, 'createdTime': createdTime, 'emails': ownerEmailList, 'day': videoDay, 'reviewed' : isReviewed}
    return videoDetails


# -------------------------------------------------------------------------------------------------
def updateAllPoints(videoDetails):
    videoName = videoDetails.get('name')
    teamName = videoDetails.get('team')
    day = videoDetails['day']

    if day is None:
        print("no day available for {}".format(videoName))
        return

    allTeamsForDay = DAILY_TEAM_POINTS[day]
    currentTeamPoints = allTeamsForDay[teamName]
    points = determinePoints(teamName)
    newPoints = currentTeamPoints + points
    allTeamsForDay[teamName] = newPoints


# -------------------------------------------------------------------------------------------------
def getDayFromVideo(videoName):
    videoDay = [day for day in DAYS_OF_THE_WEEK if day in videoName]
    if videoDay and len(videoDay) == 1:
        videoDay = videoDay[0]
    else:
        videoDay = None

    return videoDay


# -------------------------------------------------------------------------------------------------
def getPlayerFromVideo(videoName, teamPlayers):
    for playerName in teamPlayers:
        nameOptions = playerName.split(" ")
        for name in nameOptions:
            if name is not '' and name.lower() in videoName:
                return playerName

    return None


# -------------------------------------------------------------------------------------------------
def processTeamVideos(gDriveApi, teamFolders):
    allVideos = list()
    for teamFolder in teamFolders:
        teamName = teamFolder
        teamFolderId = teamFolders[teamFolder]
        videoListing = getDriveFolderContents(gDriveApi, teamFolderId, foldersOnly=False)

        for videoEntry in videoListing:
            allVideos.append(collectVideoDetails(videoEntry, teamName))

    return allVideos


# -------------------------------------------------------------------------------------------------
def main():
    global pageToken
    gdriveApi = loadDriveApi()

    print("--------------------------------------------------------------------")
    print("VanCity Pro Stay Home Stay Safe Challenge Drive Data for Week {}".format(getWeekNumber()))
    print("--------------------------------------------------------------------")
    folders = getDriveFolderContents(gdriveApi, getRootFolderId(gdriveApi))
    teamFolderInfo = dict()
    for folder in folders:
        teamFolderId = folder.get('id')
        teamFolderName = folder.get('name')
        teamFolderInfo[teamFolderName] = teamFolderId

    # collect
    allVideos = processTeamVideos(gdriveApi, teamFolderInfo)

    # update
    videosNeedFixing = dict()
    videosPendingReview = dict()
    for videoEntry in allVideos:
        if videoEntry.get('day') is None or videoEntry.get('player') is None:
            videosNeedFixing[videoEntry.get('name')] = videoEntry.get('team')
        elif videoEntry.get('reviewed'):
            updateAllPoints(videoEntry)
        else:
            videosPendingReview[videoEntry.get('name')] = videoEntry.get('team')

    if pageToken is not None:
        print("pageToken was not none, add paging")

    # summarize
    printSummary(allVideos, videosNeedFixing)
    createReport(allVideos, getChimpList(allVideos), videosPendingReview, videosNeedFixing, getWeekNumber())

    print()
    print("End")


# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
