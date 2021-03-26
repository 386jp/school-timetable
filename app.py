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
				else:
					locationText += ": " + classData["onlineURL"]
				event.add('location', locationText)

				# Event Description
				event.add('description', 'Teacher: ' + classData["classTeacher"])

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

univName = "武蔵野大学"
# 時間割
classTime = [
	{"start": "9:00", "end": "10:40"},
	{"start": "10:50", "end": "12:30"},
	{"start": "13:20", "end": "15:00"},
	{"start": "15:10", "end": "16:50"},
	{"start": "17:00", "end": "18:40"},
	{"start": "18:50", "end": "20:30"},
]
lunchBreakAfter = 2
# 学期初めの日
termStart = [
	"2021/4/9",
	"2021/5/31",
	"2021/9/24",
	"2021/11/19"
]
# 学期内の授業数
classNum = 7
# 長期休みを含む休みの日
skipDates = [
	["2021/5/21"], # 創立記念日
	["2021/7/17", "2021/9/23"], # 夏休み
	["2021/10/8", "2021/10/11"], # 摩耶祭
	["2021/11/16", "2021/11/18"], # 試験予備日
	["2021/11/23"], # 勤労感謝の日
	["2021/11/26", "2021/11/29"], # 黎明祭
	["2021/12/28", "2022/1/10"], # 冬休み
	["2022/1/14", "2022/1/16"], # 謎休み
	["2022/1/26", "2022/1/27"], # 試験予備日
	["2022/1/30", "2022/3/31"], # 春休み
]

STT = muSchoolTimetable("./timetable.csv", univName, classTime, lunchBreakAfter, termStart, classNum, skipDates)
ical = STT.generateIcal()
STT.exportIcal(ical)