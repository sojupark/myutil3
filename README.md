util for python(>3.0)

내부에서 유용하게 사용되어질 function 및 class

class MyLogger:
ptyhon 표준 패키지인 logging을 쉽게 처리할 수 있는 wrapper class 입니다.

myName, myDir, mySizeMB=100, myCount=10

1. myName
   logger 이름이자 logging file 이름입니다.
2. myDir
   logging file 위치
3. mySize
   rotate 파일 사이즈
4. myCount
   rotate 파일 갯수
-----------------------------------------------------------------------

def rsleep(myf, myt):
myf, myt 사이의 second동안 sleep

-----------------------------------------------------------------------

def rrandom(myf, myt):
myf, myt 사이의 랜덤 수 생성

-----------------------------------------------------------------------

def getMyIP():
return host ip

------------------------------------------------------------------------

class MyMultiCast():
멀티캐스트를 처리하기위한 간단한 class 입니다.

myName, isSend=True, myAddr=[]
1. myName
  미리 지정된 시스템 멀티캐스트 주소를 가져옵니다.
  myAddr=[]에 임의 멀티캐스트 주소를 설정시 의미가 없습니다.
2. isSend
   True : Sender 설정
   False : receiver 설정
3. myAddr
  설정된 멀티캐스트 주소로 그룹이 셋팅됩니다.


def send(self, msg):
msg를 보냅니다.

def recv(self):
recv
--------------------------------------------------------------------------

def getWeekDayTerm(wantWeek, fromDate, toDate=getToday()):
다음과 같은 weekday string에 해당하는 fromDate, toDate 사이의 날자리스트를 반환합니다.
['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY', 'SATURDAY']

1. wantWeek
  ['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY', 'SATURDAY']
2. fromDate
   범위시작 >=
3. toDate
   범위끝 <=

-----------------------------------------------------------------------------

def getWeek(mydate=getToday(), myf="%Y%m%d", myLang=""):
해당하는 날자의 week 값을 숫자, 영문, 한글로 return 합니다.

1. mydate
  날자값
2. myf
   1.mydate의 포맷을 결정합니다.
3. myLang
  kor : 한글
  eng : 영문
  "" : 숫자

--------------------------------------------------------------------------------

def getDeltaDate(myToday, myDeltaType='d', myDelta=0, myf="%Y%m%d"):
python 기본 timedelta의 개선 버전입니다.

--------------------------------------------------------------------------------

def getDateFromWeek(pyear, pmon, pweek_num, day_of_week_val):
pyear, pmon 의 pweek_num 번째 주의 day_of_week_val 요일에 해당하는 날자를 리턴합니다.
day_of_week_val = ['mon', 'tue', 'wed', 'thu','fri','sat','sun']

--------------------------------------------------------------------------------

def getLastDayOfMon(year, mon):
year, mon에 해당하는 캘린더데이 마지막날자를 리턴합니다.

---------------------------------------------------------------------------------

def toKorean(myt, rv=False):
myt 에 해당하는 알파벳의 한글화
rv : True 일경우 myt는 한글의 알파벳화

---------------------------------------------------------------------------------

