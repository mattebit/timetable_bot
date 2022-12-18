from __future__ import print_function

from google.auth.exceptions import MutualTLSChannelError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

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


def getService(credentials):
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


def hasCalendar(service, calendarId: str):
    calendar = getCalendar(service, calendarId)

    return not (calendar is None)


def getCalendar(service, calendarId: str):
    calendar = service.calendars().get(calendarId=calendarId).execute()
    return calendar


def addCalendar(service, name: str):
    calendar = {
        'summary': name,
        'timeZone': 'America/Los_Angeles'
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    return created_calendar
