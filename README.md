# school-timetable

時間割を記入したCSVを入力すると、ical形式で出力するPythonコード

timetable.csv.sampleにexampleが載っているので、それをtimetable.csvにrenameして、自分の履修科目を入力してください。

適宜、中身のPythonコード内、univName, classTime (時間割の時間), lunchBreakAfter (何時間目のあとに昼休みがあるか), termStart (学期のはじまりの日付), classNum (学期内の授業数), skipDates (創立記念日等学校が休みになる日)を変更してください。

一応Google Calendarにインポートできることは確認済みです

```pipenv install```

run:

```pipenv run python app.py```
