#-*-encoding:euckr-*-
import os,sys
import datetime
import calendar
import types
import re
import json
try:
	import requests
except:
	print("no requests")
import subprocess
from random import randrange
from time import sleep

import logging
import logging.handlers

sys.path.append(os.getenv("HOME")+"/svc/lib")
import mydbapi3 as mydbapi
myHOME=os.getenv("HOME")

class MyLogger:
	def __init__(self, myName, myDir, mySizeMB=100, myCount=10):
		self.logger = logging.getLogger(myName)
		FMTER = logging.Formatter('%(asctime)s|%(process)d|%(message)s')
		fileMaxByte = 1024 * 1024 * int(mySizeMB) #110MB
		myfile = myDir.rstrip("/ ")+"/"+myName+".log"
		FH = logging.handlers.RotatingFileHandler(myfile, maxBytes=fileMaxByte, backupCount=int(myCount))
		FH.setFormatter(FMTER)
		self.logger.addHandler(FH)
		self.logger.setLevel(logging.INFO)

	
	def log(self, mystr):
		self.logger.info(mystr)

def rsleep(myf, myt):
	sleep(randrange(myf,myt))

def rrandom(myf, myt):
	return randrange(myf,myt)


def getMyIP():
	import socket
	return socket.gethostbyname(socket.gethostname())


class MyMultiCast():
	def __init__(self, myName, isSend=True, myAddr=[]):

		import socket
		import struct

		self.mydic = {'mysys':('224.76.76.76',7777), 'myfeed1':('224.77.77.77',7777), 'myfeed2':('224.78.78.78',7777)}
		self.mysock = None
		self.myg = None

		if myName in self.mydic:
			self.myg = self.mydic[myName]

		if len(myAddr) > 0:
			self.myg = tuple([myAddr[0], int(myAddr[1])])

		if self.myg is not None:
			if isSend:
				self.mysock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				ttl = struct.pack('b', 1)
				self.mysock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
			else:
				self.mysock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				self.mysock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				#self.mysock.bind(('',self.myg[1]))
				self.mysock.bind((self.myg[0],self.myg[1]))
				group = socket.inet_aton(self.myg[0])
				mreq = struct.pack('4sL', group, socket.INADDR_ANY)
				self.mysock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


	def __del__(self):
		if self.mysock is not None:
			print("socket lose")
			self.mysock.close()

	def send(self, msg):
		self.mysock.sendto(msg, self.myg)

	def recv(self):
		return self.mysock.recvfrom(8192)[0]

def getRemoteQryList(mytype, dt=''):
	reval = []
	with open(myHOME+"/svc/env/remoteqry.lst") as f:
		for l in f.readlines():
			myline = l.strip()
			if myline.find("#") != 0: # commentary
				if myline.find(mytype) == 0:
					try:
						reval = [x+dt for x in myline.split(mytype,1)[1].split(":") if len(x) > 0]
					except:
						pass
					break	
	return reval


def A2Num(data_type, srcVal):
	reVal = -9999
	try:
		if data_type == "int":
			reVal = int(srcVal)
		#elif data_type == "bigint" or data_type == "long":
		#	reVal = long(srcVal)
		elif data_type == "float" or data_type.find("decimal") != -1:
			reVal = float(srcVal)
	except:
		reVal = -9999

	return reVal


# stack
class Stack:
	def __init__(self):
		self.items = []
		self.len = 0

	def push(self, val):
		self.items.append(val)
		self.len += 1

	def pop(self):
		if self.empty():
			return None
	
		self.len -= 1
		return self.items.pop()

	def size(self):
		return self.len

	def peek(self):
		if self.empty():
			return None
		return self.items[0]

	def empty(self):
		return self.len == 0

	def __str__(self):
		return str(self.items)




# only for idcb lock system
class MyLock:
	def __init__(self, mydbms="mysql", mydb="markit"):
		self.mydbms = mydbms
		self.mydb = mydb
		self.mycon = mydbapi.Mydb(mydbms, mydb)
		self.lock_info = {}
		self.setLockInfo()
	
	def __del__(self):
		if self.mycon is not None:
			self.mycon.closeDb()
		
	def setLockInfo(self):
		items = self.mycon.exeQry("G", "select cast(inst_id as char(15)), node, field, lock_lev, lock_date, correct_val, prev_val from lock_master where lock_lev = 1")
		for item in items:
			tmpDic = {}
			if item[0] in self.lock_info:
				if item[1] in self.lock_info[item[0]]:
					self.lock_info[item[0]][item[1]].append(item[2:])
				else:
					tmpDic[item[1]] = [item[2:]]
					self.lock_info[item[0]].update(tmpDic)
			else:
				tmpDic[item[1]] = [item[2:]]
				self.lock_info[item[0]] = tmpDic

	def IsLock(self,timeStamp, inst_id, tabname, dic_col, blocktp="I"):
		if inst_id in self.lock_info:
			if tabname in self.lock_info[inst_id]:
				for items in self.lock_info[inst_id][tabname]:
					_node = items[0]
					if _node in dic_col:
						print("[%s]lock_info --> [%s][%s]" % (inst_id, tabname, _node))
						correct_val = items[3].strip()
						prev_val = items[4].strip()
						this_val = str(dic_col[items[0]]).strip()
						data_type = self.getTabInfo()[tabname][_node]
						if data_type == "str":
							pass
						else:
							correct_val = A2Num(data_type, correct_val)
							prev_val = A2Num(data_type, prev_val)
							this_val = A2Num(data_type, this_val)

						print("correct_val[%s], prev_val[%s], this_val[%s]" % (str(correct_val),str(prev_val),str(this_val)))	
						if correct_val != this_val and prev_val != this_val:
							sql = """insert into lock_data_skipped values
								(%s, "%s", "%s", "%s", "%s", "%s", "%s")""" % (inst_id, tabname, items[0], timeStamp[:10].replace("-",""), timeStamp[11:19].replace(":",""), str(this_val), blocktp)
							try:	
								self.mycon.exeQry("G", sql)
								print("[%s]" % (sql))
							except:
								print(sql)
								print(sys.exc_info())
						
						print("del rev data[%s] : %s" % (items[0], dic_col[items[0]]))
						del dic_col[items[0]]
	
		return dic_col
	


	
				

#def getModText4Xlrd(x):
#	return str("%f" % x).strip("0.") if type(x) is types.FloatType else x.decode("cp949").encode("euckr",'replace').strip()
	
def getDatetimeFromUTCSec(tdata, fraction=3):
	return datetime.datetime.utcfromtimestamp(float(tdata)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-(6-fraction)]

def getErrLine(mysys):
	exc_type, exc_obj, tb = mysys.exc_info()
	lineno = tb.tb_lineno
	return [lineno, exc_obj]

def getDateFormat(mys, from_myf="%Y%m%d", to_myf="%Y%m%d"):
	return datetime.datetime.strptime(mys, from_myf).strftime(to_myf)

def getToday(myf="%Y%m%d"):
	return datetime.datetime.now().strftime(myf)

def getDateFF(mydate, myf="%Y%m%d", myt="%Y%m%d"):
	return datetime.datetime.strptime(mydate, myf).strftime(myt)

def getYear(mydate, myf="%Y%m%d"):
	mytime1 = datetime.datetime.strptime(mydate, myf)
	return mytime1.year

def getMon(mydate, myf="%Y%m%d"):
	mytime1 = datetime.datetime.strptime(mydate, myf)
	return mytime1.month

def getDay(mydate, myf="%Y%m%d"):
	mytime1 = datetime.datetime.strptime(mydate, myf)
	return mytime1.day

def getWeekDayTerm(wantWeek, fromDate, toDate=getToday()):
	datelist = ['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY', 'SATURDAY']

	reVal = []
	while fromDate <= toDate:
		if int(getWeek(fromDate)) == datelist.index(wantWeek):
			reVal.append(fromDate)
		fromDate = getDeltaDate(fromDate, 'd', 1)

	return reVal

def getWeek(mydate=getToday(), myf="%Y%m%d", myLang=""):
	myLangDic = {
			'0':{'eng':'Sun', 'kor':'일'}
			, '1':{'eng':'Mon','kor':'월'}
			, '2':{'eng':'Tue','kor':'화'}
			, '3':{'eng':'Wed','kor':'수'}
			, '4':{'eng':'Thu','kor':'목'}
			, '5':{'eng':'Fri','kor':'금'}
			, '6':{'eng':'Sat','kor':'토'}
		}
	
	reVal = datetime.datetime.strptime(mydate, myf).strftime("%w")
	if myLang != "":
		reVal = myLangDic[reVal][myLang.lower()]
	return reVal


def getDeltaDate(myToday, myDeltaType='d', myDelta=0, myf="%Y%m%d"):
	mytime1 = datetime.datetime.strptime(myToday, myf)
	myDeltaType = myDeltaType.lower()
	reVal = ""
	if myDeltaType == 'd':
		reVal = (mytime1 + datetime.timedelta(days=myDelta)).strftime(myf)
	elif myDeltaType == 'w':
		reVal = (mytime1 + datetime.timedelta(weeks=myDelta)).strftime(myf)
	elif myDeltaType == 'm':
		myyear = mytime1.year
		mymon = mytime1.month
		myday = mytime1.day

		myoper = "+"
		if myDelta < 0:
			myoper = "-"

		myyear = eval("%d%s%d" % (myyear, myoper, abs(myDelta)/12))
		mymon = eval("%d%s%d" % (mymon, myoper, abs(myDelta)%12))
		if mymon <= 0:
			myyear-=1
			mymon+=12
		elif mymon >= 13:
			myyear+=1
			mymon-=12

		# correct the last day of the month
		tmp_date = datetime.datetime(myyear,mymon,1)
		last_day = calendar.monthrange(tmp_date.year, tmp_date.month)[1]
		if last_day < myday:
			myday = "%02d"%last_day

		if myyear < 0: # first default year
			myyear = 1901
		elif myyear > 9999: # last default year
			myyear = 9999

		
		reVal = datetime.datetime.strptime("%04d%02d%s" % (myyear, mymon, myday), "%Y%m%d").strftime(myf)
	elif myDeltaType == 'y':
		myyear = mytime1.year+myDelta
		mymon = mytime1.month
		myday = mytime1.day


		# correct the last day of the month
		tmp_date = datetime.datetime(myyear,mymon,1)
		last_day = calendar.monthrange(tmp_date.year, tmp_date.month)[1]
		if last_day < myday:
			myday = "%02d"%last_day

		if myyear < 0: # first default year
			myyear = 1901
		elif myyear > 9999: # last default year
			myyear = 9999


		reVal = datetime.datetime.strptime("%04d%s%s" % (myyear, mymon, myday), "%Y%m%d").strftime(myf)
	return reVal


def getDateFromWeek(pyear, pmon, pweek_num, day_of_week_val):
	year = int(pyear)
	month = int(pmon)
	week_number = int(pweek_num)
	day_of_week_str = ['mon', 'tue', 'wed', 'thu','fri','sat','sun']
	day_of_week = day_of_week_str.index(day_of_week_val.lower())

	# Get the first day of the month
	first_day = datetime.date(year, month, 1)
	
	# Find the first occurrence of the specified day of the week in the month
	first_day_of_week = first_day + datetime.timedelta((day_of_week - first_day.weekday()) % 7)
	
	# Calculate the date by adding weeks and days
	target_date = first_day_of_week + datetime.timedelta(weeks=week_number - 1)
	
	# Check if the target date is still within the same month
	if target_date.month != month:
		raise ValueError("Invalid week number")

	return getDateFormat(str(target_date), from_myf="%Y-%m-%d", to_myf="%Y%m%d")

# Example usage:
#year = 2024
#month = 3
#week_number = 2  # The second week of the month
#day_of_week = 2  # 0 is Monday, 1 is Tuesday, ..., 6 is Sunday
#result_date = get_date_from_week(year, month, week_number, day_of_week)
#print("Date corresponding to week {} of month {} is: {}".format(week_number, month, result_date))

def getLastDayOfMon(year, mon):
	return str(calendar.monthrange(int(year),int(mon))[1])
	


def getDeltaDayStr(srcDay,mydays=1,strtype=1):
	goDate = srcDay
	mytime1 = datetime.datetime.strptime(goDate, "%Y%m%d")
	goDate2 = (mytime1 + datetime.timedelta(days=mydays)).strftime("%Y%m%d")
	if strtype == 1:
		goDate = goDate + "," + goDate2
	else:
		goDate = goDate2
	return  goDate


def getPlusDayStr(srcDay):
	goDate = srcDay
	mytime1 = datetime.datetime.strptime(goDate, "%Y%m%d")
	goDate2 = (mytime1 + datetime.timedelta(days=1)).strftime("%Y%m%d")
	goDate = goDate + "," + goDate2
	return  goDate


def getDiffRate(pthisVal, pprevVal):
	thisVal = float(pthisVal)
	prevVal = float(pprevVal)
	valtp = '0'
	val = -9999
	if prevVal == 0:
		valtp = '0'
	elif thisVal < 0 and prevVal < 0:
		if thisVal > prevVal:
			valtp = '2'
		else:
			valtp = '4'
	elif thisVal > 0 and prevVal < 0:
		valtp = '1'
	elif thisVal < 0 and prevVal > 0:
		valtp = '3'
	else:
		val = (thisVal - prevVal) / prevVal * 100.00
	return [val, valtp]

	
def getSpecialStr(myStr, myDic={}):
	if len(myDic) > 0:
		for mySrc in re.findall("\${.[^\${]+}", myStr):
			myKey = mySrc.strip("${}")
			if myKey == "sendfile_contents": # contents in sendfile
				with open(myDic['send_file'], 'r', encoding=myDic['c_file_encoding']) as fd:
					myDic['sendfile_contents'] = repr(fd.read())
			
			myStr = myStr.replace(mySrc, myDic[myKey])
	else:
		spVarList = [ 
				 "\${KWEEKDAY[_\+]+\d+[d,m,y,w,D,M,Y,W]}"
				 ,"\$KWEEKDAY[_\+]+\d+[d,m,y,w,D,M,Y,W]"
				, "\${KWEEKDAY}"
				, "\$KWEEKDAY"
				 ,"\${EWEEKDAY[_\+]+\d+[d,m,y,w,D,M,Y,W]}"
				 ,"\$EWEEKDAY[_\+]+\d+[d,m,y,w,D,M,Y,W]"
				, "\${EWEEKDAY}"
				, "\$EWEEKDAY"
				 ,"\${WEEKDAY[_\+]+\d+[d,m,y,w,D,M,Y,W]}"
				 ,"\$WEEKDAY[_\+]+\d+[d,m,y,w,D,M,Y,W]"
				, "\${WEEKDAY}"
				, "\$WEEKDAY"
				, "\${TODAY[_\+]+\d+[d,m,y,w,D,M,Y,W],[\'\"].[^\"\']+[\'\"]}"
				, "\${TODAY[_\+]+\d+[d,m,y,w,D,M,Y,W]}"
				, "\$TODAY[_\+]+\d+[d,m,y,w,D,M,Y,W]"
				, "\${TODAY,[\'\"].[^\"\']+[\'\"]}"
				, "\${TODAY}"
				, "\$TODAY"
				, "\${LOCAL_BIZ_DAY_\d+[d,m,y,w,D,M,Y,W],[\'\"].[^\"\']+[\'\"]}"
				,"\${LOCAL_BIZ_DAY_\d+[d,m,y,w,D,M,Y,W]}"
				,"\$LOCAL_BIZ_DAY_\d+[d,m,y,w,D,M,Y,W]"
				, "\${LOCAL_BIZ_DAY,[\'\"].[^\"\']+[\'\"]}"
				, "\${LOCAL_BIZ_DAY}"
				, "\$LOCAL_BIZ_DAY"
			]
		myToday = getToday()
		myFullTime = getToday("%H%M%S")

		for myTarget in spVarList:
			for checkstr in re.findall(myTarget, myStr):
				#print(myTarget, checkstr)
				mySub = ""
				if myTarget.find("LOCAL_BIZ_DAY") != -1:
					with mydbapi.Mydb("alti", "infomax","m7") as mycon:
						# LOCAL_BIZ_DAY
						sql = "SELECT sdate FROM CM2100MB WHERE sBizType='1' order by sdate desc limit 1"
						items = mycon.exeQry("G1", sql)
						if items is None:
							raise
						else:
							mySub = items[0]


						if myTarget.find("_\d+[d,m,y,w,D,M,Y,W]") != -1: # date diff
							mydelta, mydeltaTp = re.findall("(\d+)(\w)", checkstr.split("_").pop()).pop()
							sql = "SELECT sdate FROM CM2100MB WHERE sBizType='1' and sdate <= {} order by sdate desc limit 1".format(getDeltaDate(mySub, mydeltaTp, -int(mydelta)))
							items = mycon.exeQry("G1", sql)
							if items is None:
								raise
							else:
								mySub = items[0]
				else:
					mySub = myToday
					if myTarget.find("[_\+]+\d+[d,m,y,w,D,M,Y,W]") != -1: # date diff
						if checkstr.find("_") != -1:
							mydelta, mydeltaTp = re.findall("(\d+)(\w)", checkstr.split("_").pop()).pop()
							mySub = getDeltaDate(mySub, mydeltaTp, -int(mydelta))
						else:
							mydelta, mydeltaTp = re.findall("(\d+)(\w)", checkstr.split("+").pop()).pop()
							mySub = getDeltaDate(mySub, mydeltaTp, int(mydelta))
					

					if myTarget.find("WEEKDAY") != -1:
						myLang = ""
						if myTarget.find('KWEEK') != -1:
							myLang = 'kor'
						elif myTarget.find('EWEEK') != -1:
							myLang = 'eng'
								
						mySub = getWeek(mySub, myLang=myLang)
						

				# check date format
				if myTarget.find("{") != -1:
					if myTarget.replace("[d,m,y,w,D,M,Y,W]","").find(",") != -1:
						mySub = mySub + myFullTime
						myStr = myStr.replace(checkstr.strip(), getDateFF(mySub, myf='%Y%m%d%H%M%S', myt=checkstr.split(",")[1].strip("\"\'}")))
					else:
						myStr = myStr.replace(checkstr.strip(), mySub)
				else:
					myStr = myStr.replace(checkstr.strip(), mySub)
	return myStr


def checkCrontab(myckvaldic):
	# myckvaldic
	# key ['c_week','c_mon','c_day','c_hour','c_min']
	# set the crontab style in linux
	# if pass, return isGo(True)
	mydatestr = getToday("%Y%m%d%H%M%w")
	nowseq = ['c_week','c_mon','c_day','c_hour','c_min']
	
	mynowval = [mydatestr[8+4], mydatestr[:2+4], mydatestr[2+4:4+4], mydatestr[4+4:6+4], mydatestr[6+4:8+4]]
	nowvaldic = dict(zip(nowseq, mynowval))
	
	reVal = {'isGO':True, 'procDate':mydatestr}
	reVal.update({k:0 for k in nowseq})

	myCkDic = {}
	myCkDic = dict(zip(nowseq,[False]*len(nowseq)))

	try:
		for myck in nowseq:
			if myckvaldic[myck].strip().lower() == 'x' or myckvaldic[myck].strip() == '':
				# not execute
				break
			elif myck not in myckvaldic or myckvaldic[myck] == '*':
				myCkDic[myck] = True
				reVal[myck] = 0
			else:
				i = 0
				for mytime in myckvaldic[myck].split(","):
					if mytime.find("-") != -1: #range
						if int(nowvaldic[myck]) >= int(mytime.split('-')[0]) and int(nowvaldic[myck]) <= int(mytime.split('-')[1]):
							myCkDic[myck] = True
							break
					elif mytime.find("*/") != -1: #repeat
						if (int(nowvaldic[myck]) % int(mytime.replace("*/",""))) == 0:
							myCkDic[myck] = True
							break
					else:
						if int(nowvaldic[myck]) == int(mytime):
							myCkDic[myck] = True
							break
					i+=1

				if myCkDic[myck]:
					reVal[myck] = i
	except:
		print(getErrLine(sys))
		raise

	for key, val in myCkDic.items():
		if val == False:
			reVal['isGO'] = False

	return reVal


# lock system
class MyLockA:
	def __init__(self, mydb):
		self.mydb = mydb
		self.mycon = mydbapi.Mydb('mysql', 'mylock')
		self.lock_info = {}
		self.tab_info = {}
		self.setLockInfo()
	
	def __del__(self):
		if self.mycon is not None:
			self.mycon.closeDb()
		
	def setLockInfo(self):
		with mydbapi.Mydb('mysql', self.mydb) as tmpcon:
			self.tab_info = tmpcon.getTabInfo()

		items = self.mycon.exeQry("G", "select myid, node, field, correct_val, prev_val from lock_master where mydb='{mydb}' and lock_status = 'L'".format(mydb=self.mydb), useDict=True)
		for item in items:
			tmpDic = {}
			if item['myid'] in self.lock_info:
				if item['node'] in self.lock_info[item['myid']]:
					self.lock_info[item['myid']][item['node']].update({item['field']:item['correct_val']})
				else:
					tmpDic[item['node']] = {item['field']:item['correct_val']}
					self.lock_info[item['myid']].update(tmpDic)
			else:
				tmpDic[item['node']] = {item['field']:item['correct_val']}
				self.lock_info[item['myid']] = tmpDic

	def IsLock(self, myid, tabname, rdic_col, IS_PRINT=False):
		dic_col = {}
		dic_col.update(rdic_col)
		if myid in self.lock_info:
			if tabname in self.lock_info[myid]:
				for k,v in rdic_col.items():
					if k in self.lock_info[myid][tabname]:
						correct_val = self.lock_info[myid][tabname][k].strip()
						this_val = str(v).strip()
						data_type = self.tab_info[tabname][k]
						if data_type == "str":
							pass
						else:
							correct_val = A2Num(data_type, correct_val)
							this_val = A2Num(data_type, this_val)

						#print("correct_val[%s], prev_val[%s], this_val[%s]" % (str(correct_val),str(prev_val),str(this_val)))	
						if correct_val != this_val:
							try:	
								self.mycon.exeQry("G", "insert into lock_data(mydb,myid,node,field,val) values('{mydb}','{myid}','{node}','{field}','{val}')".format(mydb=self.mydb, myid=myid, node=tabname,field=k, val=v), IS_PRINT=IS_PRINT)
							except:
								pass
						del dic_col[k]
						print("del rev data[%s][%s]" % (k, v))
	
		return dic_col
	

def sms(myDears, mySMS, reverse=False, botName=''):
	mySMS = mySMS.replace("\"",'\\\\\\\\\\\\\\"').replace("\n","\\\\\\n").replace(")","\)").replace("(","\(").replace("'","\\'").replace("<","\<").replace(">","\>").replace("#","\#").replace("`","\\\\\`").replace("&","\&").replace("|","\|").replace("*","\*").replace("\t","\\\\\\t").replace(";","\;").replace("\r","").replace("$","\$").replace("{","\{").replace("}","\}")
	for myDear in myDears.split(","):
		if reverse:
			subprocess.call("ssh sp1 sms_u %s \"%s\" %s" %(myDear, mySMS, botName), shell=True)
		else:
			subprocess.call("ssh sp1 sms %s \"%s\" %s" %(myDear, mySMS, botName), shell=True)
	

def toKorean(myt, rv=False):
	pronunciation_dict = {
        	'H': '에이치',
		'A': '에이',
        	'I': '아이',
        	'J': '제이',
        	'K': '케이',
        	'V': '브이',
        	'Y': '와이',
        	'B': '비',
        	'C': '씨',
        	'D': '디',
        	'E': '이',
        	'F': '에프',
        	'G': '지',
        	'L': '엘',
        	'M': '엠',
        	'N': '엔',
        	'O': '오',
        	'P': '피',
        	'Q': '큐',
        	'R': '알',
        	'S': '에스',
        	'T': '티',
        	'W': '더블유',
        	'U': '유',
        	'X': '엑스',
        	'Z': '지'
	}

	r = ''.join([pronunciation_dict.get(char.upper(), char) for char in myt])
	if rv:
		revert_dict = {v:k for k,v in pronunciation_dict.items()}
		r = myt
		for k,v in revert_dict.items():
			r = r.replace(k,v)
		#r = ''.join([revert_dict.get(char.upper(), char) for char in myt])

	return r


def setISdata(mycurlist, sDate, dateType, dicVal={}):
	dateStr = ""

	if dateType == 'w':
		dateStr = "AND week_flag = '1'"
	elif dateType == 'm':
		dateSTr = "AND month_flag = '1'" 
	elif dateType == 't':
		dateStr = "AND term_flag = '1'"
	elif dateType == 'y':
		dateStr = "AND year_flag = '1'"

	sql = "SELECT MIN(date) FROM KL_DATE2 WHERE date >= '%s' %s" % (sDate, dateStr)

	weekDate = ""
	try:
		weekDate = mycurlist[0].exeQry("G1", sql, IS_PRINT=True)[0]
	except:
		print("weekDate[%s]" % (weekDate))

	for actcd, val in dicVal.items():
		for mServ in mycurlist:
			mServ.exeQry("I", 'ea_black_raw', {'cd':actcd, 'date':sDate, 'value':val}, IS_PRINT=True)
			mServ.exeQry("I", 'ea_black', {'cd':actcd, 'date':weekDate, 'rawdate':sDate, 'value':val}, IS_PRINT=True)



def getTIO(inputDic, isDev=False):
	headers  = {"Content-Type":"application/json"}

	#default
	param = {
		"project":"myfeed"
		, "userip":"0.0.0.0"
		, "TR":""
		, "InBlock":{}
	}

	param.update(inputDic)

	r = None
	if isDev:
		r = requests.post("http://190.1.150.205:3502/infomax/api/{}".format(inputDic['TR']), headers=headers, data=json.dumps(param))
	else:
		r = requests.post("https://api.einfomax.co.kr/infomax/api/{}".format(inputDic['TR']), headers=headers, data=json.dumps(param))

	return {"input":param, "output":r.json()}
