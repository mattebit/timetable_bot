import io
import logging
import os
import pickle
import threading
from enum import Enum
from os.path import isfile
from typing import List, Tuple, cast

from dotenv import load_dotenv
from ics import Calendar
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InvalidCallbackData,
    PicklePersistence, ConversationHandler, MessageHandler, filters,
)

# Do not change the order of the imports
import common.classes.lecture as lecture
import common.methods.unitn_activities as unitn_activities
import common.classes.user as user
import common.methods.google as google
import common.classes.course as course
from common.methods.utils import University
from common.methods.unibz_parse import fetch_cache_unibz_courses

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
UNIBZ_CACHE_FILE_PATH = "cache.pickle"
unibz_courses : list[course.Course] = []

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class link_google_states(Enum):
    START = 0
    INSERT_CODE = 1


def update_course_task(context):
    user_info : user.Userinfo = context.user_data['userinfo']

    if len(user_info.follwoing_courses) == 0:
        return

    #before = user_info.follwoing_courses

    for c in user_info.follwoing_courses:
        if c.university == University.UNITN:
            c.lectures = unitn_activities.fetch_unitn_lectures(c)

    # TODO: Send message if course list changed
    # TODO: trigger update of unibz courses
    # Unibz lectures should be already present in course


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["userinfo"] = user.Userinfo()

    chat_id = update.message.chat_id
    context.job_queue.run_repeating(update_course_task,
                                    3600,
                                    chat_id=chat_id,
                                    user_id=context._user_id,
                                    name=str(chat_id))

    await update.message.reply_text(
        'Hey, type /help for more info'
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(
        "Use /start to test this bot. Use /clear to clear the stored data so that you can see "
        "what happens, if the button data is not available. "
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears all the user data and access tokens"""
    context.user_data['userinfo'] = None

    # Removes scheduled tasks for the user
    try:
        job = context.job_queue.get_jobs_by_name(str(update.message.chat_id))
        job[0].schedule_removal()
    except:
        pass

    # TODO: Ask before clearing
    await update.effective_message.reply_text("All clear!")


async def clear_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears all the user data and access tokens"""
    userinfo: user.Userinfo = context.user_data['userinfo']
    userinfo.follwoing_courses = []
    # TODO: Ask before clearing
    await update.effective_message.reply_text("Courses cleared!")


async def add_unitn_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    courses_list = unitn_activities.list_attivita_to_list_courses(
        unitn_activities.filter_activities(unitn_activities.fetch_activities(), query))

    if len(courses_list) == 0:
        await update.message.reply_text("No activities found")
        return

    await update.message.reply_text("Choose a course to follow:",
                                    reply_markup=build_keyboard(courses_list))


async def add_unibz_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    query = query.lower()
    l : list[course.Course] = []

    for c in unibz_courses:
        if query in c.name.lower():
            l.append(c)

    if len(unibz_courses) == 0:
        await update.message.reply_text("No activities found")
        return

    await update.message.reply_text("Choose a course to follow:",
                                    reply_markup=build_keyboard(l))

async def list_following_courses(update, context):
    """
    Lists the courses the user is follwoing, grouping them by university
    """
    userinfo: user.Userinfo = context.user_data['userinfo']

    # Also trigger the update task
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(update_course_task,
                                    3600,
                                    chat_id=chat_id,
                                    user_id=context._user_id,
                                    name=str(chat_id))

    res = ""

    courses_by_uni = course.group_courses_by_uni(userinfo.follwoing_courses)

    for uni in courses_by_uni.keys():
        res += f"{uni.name}:\n"
        for c in courses_by_uni.get(uni):
            res += f"- {c.name}\n"

    await update.message.reply_text(
        f"You are following these courses:\n{res}"
    )


def build_keyboard(current_list: List[course.Course]) -> InlineKeyboardMarkup:
    """Helper function to build the inline keyboard from a list"""
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(str(i.name), callback_data=(i, current_list))
         for i in current_list]
    )


async def keyboard_course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""

    userinfo: user.Userinfo = context.user_data["userinfo"]

    query = update.callback_query
    await query.answer()
    # Get the data from the callback_data.
    # If you're using a type checker like MyPy, you'll have to use typing.cast
    # to make the checker get the expected type of the callback_data

    l: lecture.Lecture
    c, courses_list = cast(Tuple[course.Course, list[course.Course]], query.data)

    if c in userinfo.follwoing_courses:
        await query.edit_message_text(f"Your are already following the lectures of {course.name}")
        return

    if c.university == University.UNITN:
        c.lectures = unitn_activities.fetch_unitn_lectures(c)
    # Unibz lectures should be already present in course

    if len(c.lectures) == 0:
        await query.edit_message_text("No lectures found in the near future")
        return

    userinfo.follwoing_courses.append(c)

    await query.edit_message_text(
        str(f"You are now following the course {c.name}")
    )

    # we can delete the data stored for the query, because we've replaced the buttons
    context.drop_callback_data(query)


async def export_ics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Export all the user lectures to an ICS file and return it to the user.
    Args:
        update: the update object
        context: the context object
    """
    userinfo: user.Userinfo = context.user_data["userinfo"]

    cal = Calendar()

    for i in userinfo.get_all_lectures():
        cal.events.add(i.event)

    f = io.BytesIO(bytes(str(cal.serialize()), 'utf-8'))

    await context.bot.send_document(
        update.message.chat_id,
        document=f,
        filename="calendar.ics"
    )


async def sync_google(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userinfo: user.Userinfo = context.user_data["userinfo"]
    google.update_lectures_to_calendar(userinfo)
    await update.message.reply_text(
        'Calendar updated'
    )


async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informs the user that the button is no longer available."""
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Sorry, I could not process this button click 😕 Please send /start to get a new keyboard."
    )


async def google_link_account(update, context):
    flow, auth_url = google.start_flow()
    context.user_data["userinfo"].flow = flow
    await update.message.reply_text(
        'Please go to this URL: {}'.format(auth_url) + "\n" +
        "Once you got the code, send it to me please"
    )
    return link_google_states.INSERT_CODE


async def google_get_code(update, context):
    flow = context.user_data["userinfo"].flow
    context.user_data["userinfo"].flow = None
    if flow is None:
        await update.message.reply_text(
            'error, please try again'
        )
        return ConversationHandler.END

    flow = google.end_flow(flow, update.message.text)
    # context.user_data["userinfo"].flow = flow
    context.user_data["userinfo"].credentials = flow.credentials
    await update.message.reply_text(
        'Google account linked!'
    )

    return ConversationHandler.END


async def cancel(update, context):
    # context.user_data["userinfo"].flow = None
    # context.user_data["userinfo"].credentials = None
    await update.message.reply_text(
        'interrupted.'
    )
    return ConversationHandler.END


async def add_google_calendar(update, context):
    userinfo: user.Userinfo = context.user_data["userinfo"]
    if userinfo.has_calendar:
        await update.message.reply_text(
            "You already have a connected calendar"
        )
        return

    if userinfo.credentials is None:
        await update.message.reply_text(
            "You have to link your google account before adding a calendar"
        )
        return

    service = google.getService(userinfo.credentials)
    calendar = google.addCalendar(service, "timetable_bot")
    userinfo.has_calendar = True
    userinfo.calendar_id = calendar['id']
    await update.message.reply_text(
        "I successfuly created calendar on your google account\n" +
        f"calendar ID: {userinfo.calendar_id}"
    )


def load_unibz_cache():
    global unibz_courses

    if not isfile(UNIBZ_CACHE_FILE_PATH):
        print("Cache file not found, fetching unibz lectures for the first time.\nThis could take a while")
        fetch_cache_unibz_courses(UNIBZ_CACHE_FILE_PATH)

    with open(UNIBZ_CACHE_FILE_PATH, "rb") as f:
        unibz_courses = pickle.load(f)


def store_unibz_cache():
    global unibz_courses
    with open(UNIBZ_CACHE_FILE_PATH, "wb") as f:
        pickle.dump(unibz_courses, f, pickle.HIGHEST_PROTOCOL)

def main() -> None:
    """Run the bot."""
    # We use persistence to demonstrate how buttons can still work after the bot was restarted
    persistence = PicklePersistence(filepath="timetable_bot_data")
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("clear_courses", clear_courses))
    # TODO: remove course

    # Unitn commands
    application.add_handler(CommandHandler("follow_unitn_course", add_unitn_course))

    # Unibz commands
    application.add_handler(CommandHandler("follow_unibz_course", add_unibz_course))

    # General
    application.add_handler(CommandHandler("list_following_courses", list_following_courses))
    application.add_handler(CommandHandler("export_ics", export_ics))

    # Google calendar commands
    application.add_handler(CommandHandler("add_google_calendar", add_google_calendar))
    application.add_handler(CommandHandler("sync_google", sync_google))

    # SSO with google
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("link_google", google_link_account)],
        states={
            link_google_states.INSERT_CODE: [MessageHandler(filters.Regex(".*"), google_get_code)],
        }
        ,
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Handler for invalid callback data
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button,
                             pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(keyboard_course_callback))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    #sys.path.append("src")
    #load_unibz_cache()
    t = threading.Thread(target=load_unibz_cache)
    t.start()

    main()
    #store_unibz_cache()s