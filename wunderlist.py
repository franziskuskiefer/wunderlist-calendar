#!/usr/bin/python

import httplib2 as http
import json
from urlparse import urlparse

import gdata.calendar.data
import gdata.calendar.client
import gdata.acl.data
import atom
import getopt
import sys
import string
import time

import getpass

class Wunderlist:
	
	def __init__(self, email, password):

		self.uri = 'https://api.wunderlist.com'
		self.loginPath = '/login'
		self.tasksPath = '/me/tasks'
		self.listsPath = '/me/lists'
		self.remindersPath = '/me/reminders'

		
		authToken = self.login(email, password)['token']
		self.headers = {
			'Accept': 'application/json',
			'Content-Type': 'application/json; charset=UTF-8',
			'Authorization': 'Bearer '+authToken
		}
		

	def login(self, email, password):
		target = urlparse(self.uri+self.loginPath+"?email="+email+"&password="+password)
		method = 'POST'
		body = ''
		headers = {
			'Accept': 'application/json',
			'Content-Type': 'application/json; charset=UTF-8'
		}

		h = http.Http()

		response, content = h.request(target.geturl(), method, body, headers)

		data = json.loads(content)

		return data

	def getData(self, path):
		target = urlparse(self.uri+path)
		method = 'GET'
		body = ''

		h = http.Http()

		response, content = h.request(target.geturl(), method, body, self.headers)

		data = json.loads(content)

		return data

	def getTaskData(self):
		return self.getData(self.tasksPath)

	def getListData(self):
		return self.getData(self.listsPath)

class gCalendar:
	def __init__(self, email, password):
		self.cal_client = gdata.calendar.client.CalendarClient(source='Franziskus-Wunderlist.py-0.1')
		self.cal_client.ClientLogin(email, password, self.cal_client.source);
		self.calId = self.getWunderlistCalendar().split("/")[-1]

		# feed that holds all the batch rquest entries
		self.request_feed = gdata.calendar.data.CalendarEventFeed()

	def InsertSingleEvent(self, title, content='', start_time=None, end_time=None, where=''):
		event = gdata.calendar.data.CalendarEventEntry()
		event.title = atom.data.Title(text=title)
		event.content = atom.data.Content(text=content)
		event.where.append(gdata.calendar.data.CalendarWhere(value=where))

		event.when.append(gdata.calendar.data.When(start=start_time, end=end_time))

		calUrl = "http://www.google.com/calendar/feeds/"+self.calId+"/private/full"
		new_event = self.cal_client.InsertEvent(event, calUrl)

		print 'New event inserted'
		return new_event

	def addEventToBatch(self, title, content='', start_time=None, end_time=None, where=''):
		event = gdata.calendar.data.CalendarEventEntry()
		event.title = atom.data.Title(text=title)
		event.content = atom.data.Content(text=content)
		event.where.append(gdata.calendar.data.CalendarWhere(value=where))

		event.when.append(gdata.calendar.data.When(start=start_time, end=end_time))

		event.batch_id = gdata.data.BatchId(text='insert-request')
		self.request_feed.AddInsert(entry=event)

		#print 'New event inserted'

	def sendBatchRequest(self):
		calUrl = "http://www.google.com/calendar/feeds/"+self.calId+"/private/full/batch"
		response_feed = self.cal_client.ExecuteBatch(self.request_feed, calUrl)

	def getWunderlistCalendar(self):
		feed = self.cal_client.GetAllCalendarsFeed()
		for i, a_calendar in enumerate(feed.entry):
			if a_calendar.title.text == "Wunderlist":
				return a_calendar.id.text

def main():
	# parse command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:], "", ["gUser=", "wUser="])
	except getopt.error, msg:
		print ('python wunderlist.py --gUser [gUsername] --wUser [wUsername]')
		sys.exit(2)

	gUser = ''
	gPw = ''
	wUser = ''
	wPw = ''

	# Process options
	for o, a in opts:
		if o == "--gUser":
			gUser = a
		elif o == "--wUser":
			wUser = a

	# ask for passwords
	print("Your Wunderlist Password Please")
	wPw = getpass.getpass()
	print("Your Google Password Please")
	gPw = getpass.getpass()

	if gUser == '' or gPw == '' or wUser == '' or wPw == '':
		print ('python wunderlist.py --gUser [gUsername] --wUser [wUsername]')
		sys.exit(2)

	# read all tasks from wunderlist 
	wunderlist = Wunderlist(wUser, wPw)
	data = wunderlist.getTaskData()
	listData = wunderlist.getListData()

	# open google calendar 'Wunderlist' and add all tasks with due dates
	cal = gCalendar(gUser, gPw)

	for todo in data:
		if todo['due_date'] is not None:
			cal.addEventToBatch(todo['title'], '', todo['due_date'], todo['due_date'])

	cal.sendBatchRequest()

if __name__ == '__main__':
	main()



