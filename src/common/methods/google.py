from __future__ import print_function

import os
from datetime import datetime

from google.auth.exceptions import MutualTLSChannelError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import Resource
from googleapiclient.discovery import build
from ics import Event

import common.classes.lecture as lecture
import common.classes.user as user

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']

def start_flow() -> (Flow, str):
    """
    Initiate an SSO flow to allow the bot to get consent to the user's google account
    Returns: the flow object needed afterwards and the url that the user needs to visit to give consent

    """
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=GOOGLE_SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    # Tell the user to go to the authorization URL.
    auth_url, _ = flow.authorization_url(prompt='consent')

    print('Please go to this URL: {}'.format(auth_url))
    return flow, auth_url


def end_flow(flow, code: str) -> Flow:
    """
    Ends the flow of an user, giving back the code retrieved during the start_flow() function
    Args:
        flow: the flow object, after the start_flow() function has been called
        code: the code given by the user

    Returns: the flow object

    """
    flow.fetch_token(code=code)
    return flow


def getService(credentials) -> Resource:
    """
    Get a service object needed by the google calendar API to do actions on the user calendar
    Args:
        credentials: the credentials of the user

    Returns:
        the service objects
    """
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
    """
    Function used to check if the given service has access to the given calendar id
    Args:
        service: the service to check
        calendarId: the id of the calendar to check

    Returns:
        True if the service has the given calendar, and has access
    """
    calendar = getCalendar(service, calendarId)

    return not (calendar is None)


def getCalendar(service: Resource, calendarId: str):
    """
    Get the Calendar object from the given resource and calendarId
    Args:
        service: the service to use to get the calendar
        calendarId: the id of the calendar to get

    Returns:
        The calendar object if found
    """
    calendar = service.calendars().get(calendarId=calendarId).execute()
    return calendar


def addCalendar(service: Resource, name: str):
    calendar = {
        'summary': name,
        'timeZone': 'Europe/Rome' # FIXME: to change based on user
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    return created_calendar


def lecture_to_google_event(lec: lecture.Lecture, timezone: str = "Europe/Rome"):
    e = lec.event

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

    return event


def update_google_event_from_lecture(event, lec: lecture.Lecture):
    event['summary'] = lec.event.name
    event['location'] = lec.event.location
    event['description'] = lec.event.description
    event['start']['dateTime'] = lec.event.begin.isoformat('T')
    event['end']['dateTime'] = lec.event.end.isoformat('T')

    return event


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
             lec: lecture.Lecture,
             timezone: str = 'Europe/Rome'):
    """
    Add an event to a specific calendar
    Reference: https://developers.google.com/calendar/api/v3/reference/events
    """

    event = lecture_to_google_event(lec, timezone)

    event = service.events().insert(calendarId=calendarId, body=event).execute()
    lec.calendar_event_id = event['id']
    print('Event created: %s' % (event.get('htmlLink')))
    return event


def get_all_events(service: Resource, calendarId: str):
    # cancelled events could not be retrieved check gooogle apis
    # https://developers.google.com/calendar/api/v3/reference/events/list
    # showDeleted tag set to true
    all_events = []
    page_token = None
    while True:
        events = service.events().list(calendarId=calendarId,
                                       pageToken=page_token
                                       # showDeleted=True
                                       ).execute()

        for event in events['items']:
            all_events.append(event)

        page_token = events.get('nextPageToken')
        if not page_token:
            break

    return all_events


# TODO: Update added events to calendar

def update_lectures_to_calendar(userinfo: user.Userinfo) -> None:
    """
    Update the google calendar to match the lectures followed by the user
    Args:
        userinfo: the userinfo object that contains the lectures
    """
    service = getService(userinfo.credentials)

    event_list = get_all_events(service, userinfo.calendar_id)
    lecture_list = google_event_list_to_lecture_list(event_list)

    to_add, to_update, to_remove = lecture.diff(userinfo.get_all_lectures(), lecture_list)

    # Add the events that are not present in remote calendar
    for lec in to_add:
        addEvent(service,
                 userinfo.calendar_id,
                 lec)

    # Update different events
    for lec in to_update:
        update_lecture(service, userinfo.calendar_id, lec)

    # remove events that are present in remote calendar but not in local one
    for lec in to_remove:
        delete_lecture(service, userinfo.calendar_id, lec)

    print("calendar updated")


def google_event_to_lecture(google_event) -> lecture.Lecture:
    lec = lecture.Lecture()
    lec.event = Event()

    lec.calendar_event_id = google_event['id']
    lec.event.name = google_event['summary']
    lec.event.status = google_event['status']
    # lec.event.created = google_event['created']
    # lec.event.updated = google_event['updated']
    lec.event.description = google_event['description']
    lec.event.location = google_event['location']
    lec.event.begin = datetime.fromisoformat(google_event['start']['dateTime'])
    lec.event.end = datetime.fromisoformat(google_event['end']['dateTime'])

    return lec


def google_event_list_to_lecture_list(l: list) -> list[lecture.Lecture]:
    res: list[lecture.Lecture] = []
    for e in l:
        res.append(google_event_to_lecture(e))
    return res


def delete_lecture(service: Resource, calendarId: str, lecture: lecture.Lecture):
    service.events().delete(calendarId=calendarId, eventId=lecture.calendar_event_id).execute()
    print(f"removed lecture {lecture.calendar_event_id}")


def update_lecture(service: Resource, calendarId: str, lec: lecture.Lecture):
    # First retrieve the event from the API.
    event = service.events().get(calendarId=calendarId, eventId=lec.calendar_event_id).execute()

    event = update_google_event_from_lecture(event)

    updated_event = service.events().update(calendarId=calendarId,
                                            eventId=lec.calendar_event_id,
                                            body=event).execute()

    # Print the updated date.
    print(updated_event['updated'])
