#!/usr/bin/python

import httplib2 as http
import json
from urlparse import urlparse

import getopt
import sys
import string
import time

import getpass

import gflags

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

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

class gCalendar3:
	def __init__(self, deleteD):
		self.deleteDone = deleteD

		FLAGS = gflags.FLAGS
		flow = OAuth2WebServerFlow(client_id='258727566501-7gjl9a4e5pngvmluuhf8j3ke075v7o6b.apps.googleusercontent.com', client_secret='lyTD_f0YVOUdQG6huDmfmN0d', scope='https://www.googleapis.com/auth/calendar', user_agent='WunderlistPie/0.1')
		storage = Storage('calendar.dat')
		credentials = storage.get()

		if credentials is None or credentials.invalid == True:
			credentials = run(flow, storage)

		httpCon = http.Http()
		httpCon = credentials.authorize(httpCon)

		self.service = build(serviceName='calendar', version='v3', http=httpCon)

		self.wunderlistCalendarId = self.getCalendarId()

		self.newEvents = {}
		self.modifiedEvents = {}

	def getCalendarId(self):
		wunderlistCalendarId = None

		page_token = None
		while True:
			calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
			if calendar_list['items']:
				for calendar_list_entry in calendar_list['items']:
					if calendar_list_entry['summary'] == 'Wunderlist':
						wunderlistCalendarId = calendar_list_entry['id']
						break
			page_token = calendar_list.get('nextPageToken')
			if not page_token:
				break

		print("Found Wunderlist calendar at "+wunderlistCalendarId)

		return wunderlistCalendarId

	def addEvent(self, title, content='', start_time=None, end_time=None, uid='', done=False):
		if done != None and self.deleteDone:
			pass
		else:
			newEvent = {
			  'summary': title,
			  'description': content,
			  'start': {
				'date': start_time
			  },
			  'end': {
				'date': end_time
			  },
			  #'id': uid,
			  'iCalUID': uid,
			}
			self.newEvents[uid] = newEvent

	def submitEvents(self):
		page_token = None
		eventIds = self.newEvents.keys()
		while True:
			events = self.service.events().list(calendarId=self.wunderlistCalendarId, pageToken=page_token, showDeleted=True).execute()
			if events['items']:
				for event in events['items']:
					if event['iCalUID'] in eventIds:
						if (self.newEvents[event['iCalUID']]['summary'] != event['summary'] or
							self.newEvents[event['iCalUID']]['start'] != event['start'] or
							self.newEvents[event['iCalUID']]['end'] != event['end'] or
							self.newEvents[event['iCalUID']]['iCalUID'] != event['iCalUID'] or
							('description' in event.keys() and self.newEvents[event['iCalUID']]['description'] != event['description']) or
							('description' not in event.keys() and self.newEvents[event['iCalUID']]['description'] != '')):

							self.modifiedEvents[event['id']] = event
							self.modifiedEvents[event['id']]['summary'] = self.newEvents[event['iCalUID']]['summary']
							self.modifiedEvents[event['id']]['start'] = self.newEvents[event['iCalUID']]['start']
							self.modifiedEvents[event['id']]['end'] = self.newEvents[event['iCalUID']]['end']
							self.modifiedEvents[event['id']]['description'] = self.newEvents[event['iCalUID']]['description']
							self.modifiedEvents[event['id']]['status'] = 'confirmed'
						elif event['status'] == 'cancelled':
							self.modifiedEvents[event['id']] = event
							self.modifiedEvents[event['id']]['status'] = 'confirmed'
						del self.newEvents[event['iCalUID']]
						
					elif event['status'] != 'cancelled': # event is in calendar but not anymore in wunderlist with date, so we delete it
						self.service.events().delete(calendarId=self.wunderlistCalendarId, eventId=event['id']).execute()
			page_token = events.get('nextPageToken')
			if not page_token:
				break

		for eventUid in self.newEvents.keys():
			newEvent = self.newEvents[eventUid]
			created_event = self.service.events().insert(calendarId=self.wunderlistCalendarId, body=newEvent).execute()

		for eventId in self.modifiedEvents.keys():
			updated_event = self.service.events().update(calendarId=self.wunderlistCalendarId, eventId=eventId, body=self.modifiedEvents[eventId]).execute()

def main():
	# parse command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:], "d", ["wUser=", "wPwd="])
	except getopt.error, msg:
		print ('python wunderlist.py --wUser [wUsername]')
		sys.exit(2)

	wUser = ''
	wPw = ''
	deleteDone = False

	# Process options
	for o, a in opts:
		if o == "--wUser":
			wUser = a
		elif o == "--wPwd":
			wPw = a
		elif o == "-d":
			deleteDone = True

	if wUser == '':
		print ('python wunderlist.py --wUser [wUsername]')
		sys.exit(2)

	# ask for passwords
	if wPw == "":
		print("Your Wunderlist Password Please")
		wPw = getpass.getpass()

	if wUser == '' or wPw == '':
		print ('python wunderlist.py --wUser [wUsername]')
		sys.exit(2)

	# read all tasks from wunderlist 
	wunderlist = Wunderlist(wUser, wPw)
	data = wunderlist.getTaskData()
	listData = wunderlist.getListData()

	# open google calendar 'Wunderlist' and add all tasks with due dates
	cal = gCalendar3(deleteDone)

	for todo in data:
		if todo['due_date'] is not None:
			content = ''
			if todo['note'] is not None:
				content = todo['note']
			cal.addEvent(todo['title'], content, todo['due_date'], todo['due_date'], todo['id'], todo['completed_at'])

	cal.submitEvents()

	
if __name__ == '__main__':
	main()



