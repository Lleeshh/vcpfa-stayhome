from __future__ import print_function

import copy
from collections import Counter

from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

pageToken = None
videosNeedFixing = dict()
videosPendingReview = dict()

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
def printDataSummary(allVideos):
    reviewedCount = len([vid for vid in allVideos if vid.get('reviewed')])
    print()
    print('----------------------------------------------------------------------------------------')
    print("PROGRAM STATS SUMMARY")
    print('----------------------------------------------------------------------------------------')
    print("Total Videos: {}".format(len(allVideos)))
    print("reviewedVideos: {}".format(reviewedCount))
    print("Not Reviewed: {}".format(len(allVideos)-reviewedCount))


# -------------------------------------------------------------------------------------------------
def printNotReviewedSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("VIDEOS PENDING REVIEW")
    print('----------------------------------------------------------------------------------------')
    longestLen = 0
    for videoName in videosPendingReview:
        length = videosPendingReview[videoName].__len__()
        if length > longestLen:
            longestLen = length

    for videoName in videosPendingReview:
        teamName = videosPendingReview[videoName]
        spacesCount = longestLen - teamName.__len__() + 2
        print("\t{}:{}{}".format(teamName, " "*spacesCount, videoName))


# -------------------------------------------------------------------------------------------------
def printFailedSummary():
    print()
    print('----------------------------------------------------------------------------------------')
    print("FAILED PARSING")
    print('----------------------------------------------------------------------------------------')
    for entry in videosNeedFixing:
        print("\t{} {}".format(entry, videosNeedFixing[entry]))


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
def printOwnersReport(allVideos):
    print()
    print('----------------------------------------------------------------------------------------')
    print("Owners Report")
    print('----------------------------------------------------------------------------------------')
    ownerEmails = [videoDetails.get('emails') for videoDetails in allVideos]
    ownerInfo = [email for emails in ownerEmails for email in emails]
    print(Counter(ownerInfo))


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
def getSimpleVideoDetails(videoDict, teamName):
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
    # collect
    for teamFolder in teamFolders:
        teamName = teamFolder
        teamFolderId = teamFolders[teamFolder]
        videoListing = getDriveFolderContents(gDriveApi, teamFolderId, foldersOnly=False)

        for videoEntry in videoListing:
            videoDetails = getSimpleVideoDetails(videoEntry, teamName)
            allVideos.append(videoDetails)

    # update
    for videoEntry in allVideos:
        if videoEntry.get('day') is None or videoEntry.get('player') is None:
            videosNeedFixing[videoEntry.get('name')] = videoEntry.get('team')
        elif videoEntry.get('reviewed'):
            updateAllPoints(videoEntry)
        else:
            videosPendingReview[videoEntry.get('name')] = videoEntry.get('team')

    return allVideos


# -------------------------------------------------------------------------------------------------
def main():
    global pageToken
    gdriveApi = loadDriveApi()

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

    allVideos = processTeamVideos(gdriveApi, teamFolderInfo)

    if pageToken is not None:
        print("pageToken was not none, add paging")

    printDataSummary(allVideos)
    printNotReviewedSummary()
    printFailedSummary()
    printTeamPointsForWeekSummary(allVideos)
    printOwnersReport(allVideos)
    print()
    print("End")


# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()

