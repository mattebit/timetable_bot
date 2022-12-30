from __future__ import print_function

from datetime import datetime

from google.auth.exceptions import MutualTLSChannelError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import Resource
from googleapiclient.discovery import build

from src.common.classes.lecture import Lecture

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']


def start_flow():
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=GOOGLE_SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    # Tell the user to go to the authorization URL.
    auth_url, _ = flow.authorization_url(prompt='consent')

    print('Please go to this URL: {}'.format(auth_url))
    return flow, auth_url


def end_flow(flow, code: str):
    flow.fetch_token(code=code)
    return flow


def getService(credentials) -> Resource:
    creds = credentials
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception()

    try:
        service = build('calendar', 'v3', credentials=creds)
    except MutualTLSChannelError as e:
        print(e)
        return None

    return service


def hasCalendar(service: Resource, calendarId: str) -> bool:
    calendar = getCalendar(service, calendarId)

    return not (calendar is None)


def getCalendar(service: Resource, calendarId: str):
    calendar = service.calendars().get(calendarId=calendarId).execute()
    return calendar


def addCalendar(service: Resource, name: str):
    calendar = {
        'summary': name,
        'timeZone': 'America/Los_Angeles'
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    return created_calendar


def addEvent(service: Resource,
             calendarId: str,
             name: str,
             location: str,
             description: str,
             start: datetime,
             end: datetime,
             timezone: str = 'Europe/Rome'):
    """
    Add an event to a specific calendar
    Reference: https://developers.google.com/calendar/api/v3/reference/events
    """
    event = {
        'summary': name,
        'location': location,
        'description': description,
        'start': {
            # 'dateTime': '2015-05-28T09:00:00-07:00',
            # The - is the offset, not needed if using timezone
            'dateTime': start.isoformat('T'),
            'timeZone': timezone,
        },
        'end': {
            # 'dateTime': '2015-05-28T17:00:00-07:00',
            'dateTime': end.isoformat('T'),
            'timeZone': timezone,
        },
        'recurrence': [
        ],
        'attendees': [
        ],
        'reminders': {
            'useDefault': True,
        },
    }

    event = service.events().insert(calendarId=calendarId, body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    return event

def addEvent(service: Resource,
             calendarId: str,
             lecture : Lecture,
             timezone: str = 'Europe/Rome'):
    """
    Add an event to a specific calendar
    Reference: https://developers.google.com/calendar/api/v3/reference/events
    """

    e = lecture.event

    event = {
        'summary': e.name,
        'location': e.location,
        'description': e.description,
        'start': {
            # 'dateTime': '2015-05-28T09:00:00-07:00',
            # The - is the offset, not needed if using timezone
            'dateTime': e.begin.isoformat('T'),
            'timeZone': timezone,
        },
        'end': {
            # 'dateTime': '2015-05-28T17:00:00-07:00',
            'dateTime': e.end.isoformat('T'),
            'timeZone': timezone,
        },
        'recurrence': [
        ],
        'attendees': [
        ],
        'reminders': {
            'useDefault': True,
        },
    }

    event = service.events().insert(calendarId=calendarId, body=event).execute()
    lecture.calendar_event_id = event['id']
    print('Event created: %s' % (event.get('htmlLink')))
    return event


# TODO: List events

# TODO: Update added events to calendar
