# timetable_bot
Service Design and engineering course's project

## Deploy
### Docker
Before starting, first fill your .env file with the bot token and add the `credentials.json` file from google for the SSO authentication of the client application, more info about how to get it can be found [here](https://developers.google.com/calendar/api/quickstart/python)

Then build the docker image by doing
```bash
docker build . -t timetable_bot
```

And run it by doing
```bash
docker run --name timetable_bot timetable_bot 
```

You can also detach and auto-start by doing
```bash
docker run -d --restart unless-stopped --name timetable_bot timetable_bot
```

## Documentation
The documentation of the software and the services can be found in the `docs/` folder

https://timetablebot.docs.apiary.io/#

## TODO
- [x] Write documentation of bot API
- [x] Write info about google API
- [x] Write info about unitn API
- [ ] Write report and explain how all works
- [ ] Build a dockerimage
- [ ] Separate the adapter from the backend
    
## ideas
- fetch updates on lectures every 30 minutes informing the user about changes
- Add the followed courses form a user

