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