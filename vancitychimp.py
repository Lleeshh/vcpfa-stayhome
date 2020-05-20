from __future__ import print_function

import copy
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

DRIVE_CREATE_TIME_TEMPLATE = '%Y-%m-%dT%H:%M:%S.%fZ'

printDebug = True
pageToken = None
reviewedVideos = dict()
unreviewedVideos = dict()
notFoundPlayerVids = list()
playerPointsByDay = dict()        # playerName : [7] for the days
playersData = dict()

REVIEWED_KEYWORDS = {'reviewed', 'reviwed', 'reeviewed', 'reveiwed'}
VIDEO_UPLOAD_ROOT_FOLDER = 'TEAMS (UPLOAD VIDS HERE)'

DAYS_OF_THE_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
TEAM_POINTS_TEMPLATE = {"ARSENAL FC": 0, "ATALANTA BC": 0, "BAYERN MUNICH": 0, "BORUSSIA DORTMUND": 0, "CHELSEA FC": 0, "CLUB ATHLETICO DE MADRID": 0, "FC BARCELONA": 0,  "JUVENTUS": 0, "LIVERPOOL FC": 0, "MANCHESTER CITY": 0, "OLYMPIQUE LYONNAIS": 0, "PARIS ST-GERMAIN": 0, "REAL MADRID CF": 0, "SSC NAPOLI": 0, "TOTTENHAM HOTSPURS": 0, "VALENCIA CF": 0}
DAILY_TEAM_POINTS = dict()
for day in DAYS_OF_THE_WEEK:
    DAILY_TEAM_POINTS[day] = copy.deepcopy(TEAM_POINTS_TEMPLATE)

TEAMPLAYERS = {"ARSENAL FC":["Goodluck", "Joaquim","Kai"],
               "ATALANTA BC":["Mohamed Konneh","Koben","Carter"],
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
        length = unreviewedVideos[videoName].__len__()
        if length > longestLen:
            longestLen = length

    for videoName in unreviewedVideos:
        teamName = unreviewedVideos[videoName]
        spacesCount = longestLen - teamName.__len__() + 2
        print("\t{}:{}{}".format(teamName, " "*spacesCount, videoName))


# -------------------------------------------------------------------------------------------------
def printFailedSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("FAILED PARSING")
    print('----------------------------------------------------------------------------------------')
    for entry in notFoundPlayerVids:
        print("\t{} {}".format(entry, entry))


# -------------------------------------------------------------------------------------------------
def printTeamPointsForWeekSummary():
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
def getSimpleVideoDetails(videoDict):
    videoDetails = dict()
    videoName = videoDict.get('name')
    videoName = getSanitizedVideoName((videoName))
    owners = videoDict.get('owners')

    if owners and len(owners) > 1:
        print("FAILURE: Unable to handle more than one owner! {}". videoDict)
        exit(22)
    ownerEmail = owners[0].get('emailAddress')

    if videoName in videoDetails:
        print("Video {} already exists with {}, overwriting it with {}".format(videoName, videoDetails[videoName], videoDict))

    videoDay = [day for day in DAYS_OF_THE_WEEK if day in videoName]
    if videoDay and len(videoDay) == 1:
        videoDay = videoDay[0]
    else:
        videoDay = None

    videoDetails = {'name': videoName, 'id': videoDict.get('id'), 'createdTime': videoDict.get('createdTime'), 'email': ownerEmail, 'day': videoDay}
    return videoDetails


# -------------------------------------------------------------------------------------------------
def updateAllPoints(teamName, videoDetails):
    teamPlayerList = TEAMPLAYERS[teamName]
    videoName = videoDetails['name']

    day = videoDetails['day']
    if day is None:
        return

    allTeamsForDay = DAILY_TEAM_POINTS[day]
    currentTeamPoints = allTeamsForDay[teamName]
    for playerName in teamPlayerList:
        nameOptions = playerName.split(" ")
        for name in nameOptions:
            if name is not '' and name.lower() in videoName:
                # Now we know the Team, Player, Day and Points
                points = determinePoints(teamName)
                newPoints = currentTeamPoints + points
                allTeamsForDay[teamName] = newPoints
                return

    notFoundPlayerVids.append({teamName:videoName})
    print("FAILED to parse {} video {}".format(teamName, videoDetails))


# -------------------------------------------------------------------------------------------------
def populateReviewInfo(teamName, videoEntry):
    videoName = videoEntry['name']

    if any(text in videoName for text in REVIEWED_KEYWORDS):
        # handle dupes
        # if videoName in reviewedVideos:
        #     if printDebug: print("Duplicate Video Found in Reviewed={}".format(videoName))
        reviewedVideos[videoName] = teamName
    else:
        # handle dupes
        # if videoName in unreviewedVideos:
        #     if printDebug: print("Duplicate Video Found in unreviewedVideos={}".format(videoName))
        unreviewedVideos[videoName] = teamName


# -------------------------------------------------------------------------------------------------
def processTeamVideos(gDriveApi, teamFolders):
    for teamFolder in teamFolders:
        teamName = teamFolder
        teamFolderId = teamFolders[teamFolder]
        videoListing = getDriveFolderContents(gDriveApi, teamFolderId, foldersOnly=False)

        for videoEntry in videoListing:
            videoDetails = getSimpleVideoDetails(videoEntry)
            populateReviewInfo(teamName, videoDetails)
            updateAllPoints(teamName, videoDetails)


# -------------------------------------------------------------------------------------------------
def main():
    global pageToken
    gdriveApi = loadDriveApi()

    while True:
        print("--------------------------------------------------------------------")
        print("Getting VanCity Pro Stay Home Stay Safe Virtual Challenge Drive Data")
        print("--------------------------------------------------------------------")
        uploadVidsFolderId = getRootFolderId(gdriveApi)
        folders = getDriveFolderContents(gdriveApi, uploadVidsFolderId)
        teamFolderInfo = dict()
        for folder in folders:
            teamFolderId = folder.get('id')
            teamFolderName = folder.get('name')
            teamFolderInfo[teamFolderName] = teamFolderId
            if printDebug:
                print('Found folder: {} ({})'.format(teamFolderName, teamFolderId))

        processTeamVideos(gdriveApi, teamFolderInfo)

        if pageToken is None:
            break
        break

    printDataSummary()
    printNotReviewedSummary()
    printFailedSummary()
    printTeamPointsForWeekSummary()
    print()
    print("End")


# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()

