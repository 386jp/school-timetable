# Import library
import urllib.parse
import pandas as pd
import icalendar as ic
import datetime as dt

# Define class
class muSchoolTimetable:
	def __init__(self, timetableCsv, univName, classTime, lunchBreakAfter, termStart, classNum, skipDates):
		"""convert school timetable into ical format

		Args:
			timetableCsv (string): Path to the timetable (please use format available on GitHub)
			classTime (dictionary inside list): Class timetable (format: {"start": "9:00", "end": "10:40"})
			termStart (string): Date when the class starts
			classNum (int): Number of classes in one term
			skipDates (list inside list): Dates of the break including long breaks
		"""
		df = pd.read_csv(timetableCsv)
		self.timetable = df.where(df.notnull(), None).to_dict(orient='records')

		# CSV Data Validation
		for dataId, data in enumerate(self.timetable):
			csvColumns = ["classNumber", "className", "classTerm", "classTermDuration", "classWeekday", "classTime", "classTimeDuration", "classTeacher"]
			for column in csvColumns:
				if data[column] == None:
					raise ValueError("Please enter valid CSV file: " + column + " column should not be empty. Error at: " + str(dataId))
			if (data["onlineURL"] == None) & (data["classPlace"] == None):
				raise ValueError("Please enter valid CSV file: onlineURL and classPlace value conflicts (either column should be filled). Error at: " + str(dataId))
			if (data["onlineURL"] != None) & (data["classPlace"] != None):
				raise ValueError("Please enter valid CSV file: onlineURL and classPlace value conflicts (both column should not be filled). Error at: " + str(dataId))

		# Univ Name
		self.univName = univName

		# Class Time Conversion
		self.classTime = []
		for time in classTime:
			timeStart = [int(t) for t in time["start"].split(":")]
			timeEnd = [int(t) for t in time["end"].split(":")]
			self.classTime.append({"start": dt.timedelta(hours=timeStart[0], minutes=timeStart[1]), "end": dt.timedelta(hours=timeEnd[0], minutes=timeEnd[1])})

		# Lunch Break
		self.lunchBreakAfter = lunchBreakAfter

		# Term Start Conversion
		self.termStart = []
		for termD in termStart:
			termD = [int(m) for m in termD.split("/")]
			self.termStart.append(dt.datetime(year=termD[0], month=termD[1], day=termD[2]))
		termD = [int(m) for m in termStart[0].split("/")]
		self.termStart.append(dt.datetime(year=(termD[0] + 1), month=termD[1], day=1) - dt.timedelta(days=1))

		# Class Num
		self.classNum = classNum

		# Skip Dates Conversion
		self.skipDates = []
		for dates in skipDates:
			startDate = [int(d) for d in dates[0].split("/")]
			if len(dates) == 1:
				self.skipDates.append(dt.datetime(year=startDate[0], month=startDate[1], day=startDate[2]))
			else:
				endDate = [int(d) for d in dates[1].split("/")]
				startDt = dt.datetime(year=startDate[0], month=startDate[1], day=startDate[2])
				endDt = dt.datetime(year=endDate[0], month=endDate[1], day=endDate[2])
				for i in range((endDt - startDt).days + 1):
					self.skipDates.append(startDt + dt.timedelta(i))

	def generateIcal(self):
		ical = ic.Calendar()

		for dataId, classData in enumerate(self.timetable):
			loopIsLunch = 2 if (classData["classTimeDuration"] > 1) & ((classData["classTime"] <= self.lunchBreakAfter) & ((classData["classTime"] + classData["classTimeDuration"] - 1) > self.lunchBreakAfter)) else 1
			for loopIdLunch in range(loopIsLunch):
				# Event Init
				event = ic.Event()
				event.add('uid', urllib.parse.quote("mu-timetable-" + self.univName + "_" + str(self.termStart[classData["classTerm"] - 1].strftime("%Y%m%dT%H%M%S")) + "_" + str(dataId) + "_" + str(loopIdLunch)) + '@dev.386.jp')
				event.add('dtstamp', dt.datetime.now())

				# Event Summary (Title)
				event.add('summary', '[' + classData["classNumber"] + '] ' + classData["className"])

				# Event Location
				locationText = "Online"
				if classData["onlineURL"] == None:
					locationText = self.univName + " " + classData["classPlace"]
				event.add('location', locationText)

				# Event Description
				descriptionText = 'Teacher: ' + classData["classTeacher"]
				if classData["onlineURL"] != None:
					descriptionText += "\nLink for Online Conference: " + classData["onlineURL"]
				event.add('description', descriptionText)

				# Event Time Start
				## Date
				week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
				termStartWeekday = self.termStart[classData["classTerm"] - 1].weekday()
				classStartWeekday = [wid for wid, w in enumerate(week) if w == classData["classWeekday"]][0]
				dateDelta = classStartWeekday - termStartWeekday
				if termStartWeekday > classStartWeekday:
					dateDelta = len(week) - termStartWeekday + classStartWeekday
				classDateStart = self.termStart[classData["classTerm"] - 1] + dt.timedelta(days=dateDelta)

				## Time
				classStartTime = self.classTime[classData["classTime"] - 1]["start"]
				classEndTime = self.classTime[classData["classTime"] + classData["classTimeDuration"] - 2]["end"]
				if loopIsLunch == 2:
					if loopIdLunch == 0:
						classEndTime = self.classTime[self.lunchBreakAfter - 1]["end"]
					if loopIdLunch == 1:
						classStartTime = self.classTime[self.lunchBreakAfter]["start"]

				event.add('dtstart', classDateStart + classStartTime)
				event.add('dtend', classDateStart + classEndTime)
				event.add('rrule', {'freq': 'weekly', 'until': self.termStart[classData["classTerm"] + classData["classTermDuration"] - 1] - dt.timedelta(days=1)})
				for skipDate in [d for d in self.skipDates if d.weekday() == classDateStart.weekday()]:
					event.add('exdate', skipDate + classStartTime)
				ical.add_component(event)


		ical.add('version', '2.0')
		ical.add('prodid', '-//386JP//MuSchoolTimetable//JP')
		return ical

	def exportIcal(self, ical, path="export.ics"):
		with open(path, mode='wb') as ics:
			ics.write(ical.to_ical())

univName = "???????????????"
# ?????????
classTime = [
	{"start": "8:50", "end": "10:30"},
	{"start": "10:40", "end": "12:20"},
	{"start": "13:10", "end": "14:50"},
	{"start": "15:00", "end": "16:40"},
	{"start": "16:50", "end": "18:30"},
	{"start": "18:40", "end": "20:20"},
]
lunchBreakAfter = 2
# ??????????????????
termStart = [
	"2021/4/9",
	"2021/5/31",
	"2021/9/24",
	"2021/11/19"
]
# ?????????????????????
classNum = 7
# ?????????????????????????????????
skipDates = [
	["2021/5/21"], # ???????????????
	["2021/7/17", "2021/9/23"], # ?????????
	["2021/10/8", "2021/10/11"], # ?????????
	["2021/11/16", "2021/11/18"], # ???????????????
	["2021/11/23"], # ??????????????????
	["2021/11/26", "2021/11/29"], # ?????????
	["2021/12/28", "2022/1/10"], # ?????????
	["2022/1/14", "2022/1/16"], # ?????????
	["2022/1/26", "2022/1/27"], # ???????????????
	["2022/1/30", "2022/3/31"], # ?????????
]

STT = muSchoolTimetable("./timetable.csv", univName, classTime, lunchBreakAfter, termStart, classNum, skipDates)
ical = STT.generateIcal()
STT.exportIcal(ical)