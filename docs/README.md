# timetable bot documentation
the timetable bot allows you to fetch the lecures of the courses you are following from your university APIs or website and to sync them with your google calendar. As today, only UNITN and UNIBZ are supported.

## Architecture
The architecture is as follows:
[ image ]
It features a backend which hosts a telegram bot and manages the connection with the google calendar APIs and with the adapter. The adapter service manages the different APIs or webpages of the universities and exposes an API to gather data about the lectures. The adapter will be used by the backend to fetch the lectures regularly. The telegram client will communicate via telegram to the backend by the use of commands.

## Backend (bot) API
The bot allows you to select the courses and lectures to follow and to connect to your google calendar. Following, the list of all possible commands:

- `/start` used to start the bot
- `/help` used to get information about how to use the bot
- `/clear` clear all user data contained in the bot
- `/clear_courses` remove all following courses of the user from the bot
- `/follow_unitn_course <course name>` used to follow the specified unitn course, it will first search by course name and display the occurencies
- `/follow_unibz_course <course name>` used to follow the specified unibz course, it will first search by course name and display the occurencies
- `/list_following_courses` used to list the courses the user is following
- `/export_ics` used to export an ics file containing all the lectures of the following courses
- `/link_google` used to connect a google account to the bot, in order to then connect to the google calendar
- `/add_google_calendar` used to add a dedicated google calendar for the bot in the google account linked
- `/sync_google` used to sync the google calendar with the lectures of the courses followed by the user

The backend will manage the SSO login to the google account to receive authorization to use the user's googe calendar

## Google API
All the calls to the google API has been done by the use of their client library for python [google-api-python-client](https://github.com/googleapis/google-api-python-client)

## Accessing and editing calendars
[API reference](https://developers.google.com/calendar/api/v3/reference/calendars)<br>
get and insert methods have been used

## Accessing and editing events
[API reference](https://developers.google.com/calendar/api/v3/reference/events)<br>
get, list, insert, delete methods have been used


## UNITN API
I didn't find any documentation about the Unitn API so I checked the requests from their timetable webpage and used them in the code by then parsing the response that luckly was a JSON. Following a list of useful endpoints with some very complicated url query parameters

### Endpoint to gather courses, teachers, and degrres /AgendaStudentiUnitn/combo.php
In this enpoint you can retrieve all the IDs necesssary to ask the other enpoints more information.
For example, if you want to download "Fundamental interactions" class schedule, you need to know its id. Just search for it in the json returned by this endpoint.

`https://easyacademy.unitn.it/AgendaStudentiUnitn/combo.php?sw=ec_&aa=2020&page=corsi`

> `sw=ec_` should mean _starts\_with_ = _ec\__, where _ec_ means _elective course_

You can choose between:
- Degree `page=corsi`
- Lecturer `page=docenti`
- Course `page=attivita`

The json received as a response will be different accordingly.

### Timetable endpoint /AgendaStudentiUnitn/grid_call.php
`https://easyacademy.unitn.it/AgendaStudentiUnitn/grid_call.php?view=easycourse&form-type=attivita&include=attivita&anno=2022&attivita%5B%5D=EC145660_IUPPA&visualizzazione_orario=cal&periodo_didattico=&date=10-10-2022&_lang=en&list=&week_grid_type=-1&ar_codes_=&ar_select_=&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&all_events=0&faculty_group=0&_lang=en&all_events=0&txtcurr=`

apparently it can be simplified as:
`https://easyacademy.unitn.it/AgendaStudentiUnitn/grid_call.php?view=easycourse&form-type=attivita&include=attivita&anno=2022&attivita%5B%5D=EC145660_IUPPA&visualizzazione_orario=cal&date=10-10-2022&list=&week_grid_type=-1&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&faculty_group=0&_lang=en&all_events=0`


### Endpoint to download full timetable in .ics AgendaStudentiUnitn/export/ec_download_ical_list.php
This is the full url used in the webapp:
`https://easyacademy.unitn.it/AgendaStudentiUnitn/export/ec_download_ical_list.php?view=easycourse&include=attivita&anno=2022&attivita%5B%5D=EC145660_IUPPA&visualizzazione_orario=cal&date=10-10-2022&_lang=en&highlighted_date=0&_lang=en&all_events=1&&_lang=en&ar_codes_=|EC145660_IUPPA&ar_select_=|true&txtaa=2022/2023&txtattivita=Fundamental%20Interactions%20%20[R.%20Iuppa]&corso=&cdl=&anno2=&docente=&txtcorso&txtanno&=&txtdocente=`
<br>

apparently it can be simplified just with this query parameters:
`https://easyacademy.unitn.it/AgendaStudentiUnitn/export/ec_download_ical_list.php?view=easycourse&include=attivita&anno=2022&attivita%5B%5D=EC145660_IUPPA&visualizzazione_orario=cal&date=10-10-2022&highlighted_date=0&all_events=1`
<br>

## UNIBZ webpage scraping
The page scraped was [this](https://www.unibz.it/en/timetable/).

# Useful infos
## Managing multiple users
In order to identify the user and to limit the actions it can do, we can use the id parameter of telegram.User, which is an unique identifier
https://docs.python-telegram-bot.org/en/v20.0b0/telegram.user.html#telegram.User

## Saving user infos
I'm planning to use context.user_data
https://github.com/python-telegram-bot/python-telegram-bot/wiki/Storing-bot,-user-and-chat-related-data
to make it persistant I need also this:
https://github.com/python-telegram-bot/python-telegram-bot/wiki/Making-your-bot-persistent
I'm planning to also save access tokens for google here.

## Google OAuth consent
I need to use the deprecated flow, with the code to be pasted into the application, as I'm not hosting a webserver to redirect the OAuth response
https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html#google_auth_oauthlib.flow.InstalledAppFlow

## To generate documentation with sphynx
sphinx-apidoc -f -o docs/source src
sphinx-build -b html docs/source docs/build

## Cancel an event
https://www.rfc-editor.org/rfc/rfc5545#page-92
in the Event class specify status as CANCELLED