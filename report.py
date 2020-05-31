import datetime
import os

import openpyxl
from openpyxl.styles import Font, PatternFill


# -------------------------------------------------------------------------------------------------
def setColumnWidths(sheet):
    dims = {}
    for row in sheet.rows:
        for cell in row:
            if cell.value:
                dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))))
    for col, value in dims.items():
        sheet.column_dimensions[col].width = value + int(value*0.15)
        sheet.column_dimensions[col].auto_size = True


# -------------------------------------------------------------------------------------------------
def writeHeaderRowExcel(sheet, headerNames, row=1):
    column = 1
    for value in headerNames:
        sheet.cell(row=row, column=column, value=value)
        sheet.cell(row, column).font = Font(bold=True)
        sheet.cell(row, column).fill = PatternFill(start_color='7FFFD4', fill_type='solid')
        column += 1


# -------------------------------------------------------------------------------------------------
def writeFailedParsing(sheet, videosNeedFixing):
    # Needs Fixing Review
    writeHeaderRowExcel(sheet, ['Video Name'])
    row = 2
    for videoName in videosNeedFixing:
        sheet.cell(row=row, column=1, value=videoName)

    setColumnWidths(sheet)


# -------------------------------------------------------------------------------------------------
def writePendingReview(sheet, videosPendingReview):
    # Pending Review
    writeHeaderRowExcel(sheet, ['Video Name', 'Team'])
    row = 2
    for videoName in videosPendingReview:
        teamName = videosPendingReview[videoName]
        sheet.cell(row=row, column=1, value=videoName)
        sheet.cell(row=row, column=2, value=teamName)
        row += 1

    setColumnWidths(sheet)


# -------------------------------------------------------------------------------------------------
def writeSummaryExcel(sheet, allVideos):
    # Stats Summary
    writeHeaderRowExcel(sheet, ['Total Videos', 'Reviewed', 'Unreviewed'])
    row = 2
    reviewedCount = len([vid for vid in allVideos if vid.get('reviewed')])
    sheet.cell(row=row, column=1, value=len(allVideos))
    sheet.cell(row=row, column=2, value=reviewedCount)
    sheet.cell(row=row, column=3, value=len(allVideos) - reviewedCount)
    setColumnWidths(sheet)


# -------------------------------------------------------------------------------------------------
def writeSummaryCsv(allVideos, outputPath, fileNameBase):
    import csv
    csvFieldNames = ['name', 'id', 'player', 'team', 'createdTime', 'emails', 'day', 'reviewed']
    csv_file = "{}/{}.csv".format(outputPath, fileNameBase)
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csvFieldNames)
            writer.writeheader()
            for data in allVideos:
                writer.writerow(data)
    except IOError:
        print("I/O error")


# -------------------------------------------------------------------------------------------------
def writeDataExcel(sheet, allVideos):
    # openpyxl does things based on 1 instead of 0
    headerNames = ['Video Name', 'Video Id', 'Player', 'Team', 'Video Created Time', 'Owner Emails', 'Video Day', 'Video Reviewed']
    writeHeaderRowExcel(sheet, headerNames)

    row = 2
    for entry in allVideos:
        column = 1
        for key, values in entry.items():
            # Put the key in the first column for each key in the dictionary
            if key == 'emails':
                values = ','.join(values)
            sheet.cell(row=row, column=column, value=values)
            column += 1
        row += 1

    setColumnWidths(sheet)


# -------------------------------------------------------------------------------------------------
# Unique list of players, emails, etc
def writeChimpFinalExcel(sheet, chimpList):
    playerKeys = set()
    uniqueChimpList = []
    for video in chimpList:
        player = video.get('player')
        team = video.get('team')
        playerKey = '{}-{}'.format(player, team)

        if playerKey in playerKeys:
            continue

        playerKeys.add(playerKey)
        uniqueChimpList.append(video)

    writeDataExcel(sheet, uniqueChimpList)


# -------------------------------------------------------------------------------------------------
def createReport(allVideos, chimpList, videosPendingReview, videosNeedFixing, weekNumber: int):
    now = datetime.datetime.now()
    timestamp = "{}.{}.{}.{}.{}.{}".format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    outputPath = os.path.join('output', timestamp)
    os.makedirs(outputPath)
    fileNameBase = "VanCity Pro Week {} Report".format(weekNumber)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Summary"
    writeSummaryExcel(sheet, allVideos)

    workbook.create_sheet('All Videos')
    sheet = workbook['All Videos']
    writeDataExcel(sheet, allVideos)

    workbook.create_sheet('Pending Review')
    sheet = workbook['Pending Review']
    writePendingReview(sheet, videosPendingReview)

    workbook.create_sheet('Failed Parsing')
    sheet = workbook['Failed Parsing']
    writeFailedParsing(sheet, videosNeedFixing)

    workbook.create_sheet('All Chimp Videos')
    sheet = workbook['All Chimp Videos']
    writeDataExcel(sheet, chimpList)

    workbook.create_sheet('Chimp Final')
    sheet = workbook['Chimp Final']
    writeChimpFinalExcel(sheet, chimpList)
    workbook.save(filename="{}/{}.xlsx".format(outputPath, fileNameBase))
