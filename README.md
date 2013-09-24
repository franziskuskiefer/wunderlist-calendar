Wunderlist-Calendar
===================

A simple Wunderlist-GoogleCalendar script to show ToDos in Google Calendar.

For now it allows to parse your [Wunderlist](https://www.wunderlist.com) tasks with due date and add them to a calendar named 'Wunderlist' in you google calendar.
It also updates existing evens when changed in Wunderlist. Using <code>-d</code> deletes finished tasks from the calendar and only unfinished tasks are added to the calendar.

Usage:

<pre><code>./wunderlist.py --wUser [WunderlistUser] [-d]</code></pre>

##### Dependencies

You need the google client library for python. Follow the instructions at [google](https://developers.google.com/google-apps/calendar/setup) for this.
