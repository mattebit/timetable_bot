import logging
import os
from enum import Enum
from typing import List, Tuple, cast

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InvalidCallbackData,
    PicklePersistence, ConversationHandler, MessageHandler, filters,
)

from common.classes.user import Userinfo
from common.methods.google import start_flow, end_flow, getService, addCalendar
from common.methods.unitn_activities import fetch_activities, filter_activities, fetch_lectures, \
    list_lezione_to_list_lecture, attivita_to_course, list_attivita_to_list_courses
from common.classes.unitn import Attivita, Lezione
from common.methods.utils import update_lectures_to_calendar, group_courses_by_uni
from src.common.classes.course import Course
from src.common.classes.lecture import Lecture

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class link_google_states(Enum):
    START = 0
    INSERT_CODE = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["userinfo"] = Userinfo()
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
    context.user_data = None
    #TODO: Ask before clearing
    await update.effective_message.reply_text("All clear!")


async def add_unitn_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    courses_list = list_attivita_to_list_courses(filter_activities(fetch_activities(), query))

    if len(courses_list) == 0:
        await update.message.reply_text("No activities found")
        return

    await update.message.reply_text("Choose a course to follow:",
                                    reply_markup=build_keyboard(courses_list))

async def list_following_courses(update, context):
    """
    Lists the courses the user is follwoing, grouping them by university
    """
    userinfo : Userinfo = context.user_data['userinfo']

    res = ""

    courses_by_uni = group_courses_by_uni(userinfo.follwoing_courses)

    for uni in courses_by_uni.keys():
        res += f"{uni.name}:\n"
        for course in courses_by_uni.get(uni):
            res += f"- {course.name}\n"

    await update.message.reply_text(
        f"You are following these courses:\n{res}"
    )

def build_keyboard(current_list: List[Course]) -> InlineKeyboardMarkup:
    """Helper function to build the inline keyboard from a list"""
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(str(i), callback_data=(i, current_list))
         for i in current_list]
    )

async def list_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""

    userinfo = context.user_data["userinfo"]

    query = update.callback_query
    await query.answer()
    # Get the data from the callback_data.
    # If you're using a type checker like MyPy, you'll have to use typing.cast
    # to make the checker get the expected type of the callback_data

    #FIXME: Convert it by using courses
    activity : Attivita
    activity, list_activities = cast(Tuple[Attivita, list[Attivita]], query.data)

    lectures : list[Lecture] = list_lezione_to_list_lecture(
            fetch_lectures(activity['valore'], True))

    if len(lectures) == 0:
        await query.edit_message_text("No lectures found in the near future")
        return

    if activity['valore'] in userinfo.following_activities:
        await query.edit_message_text(f"Lectures of {activity['valore']} already present in google calendar")
        return

    userinfo.following_activities[activity['valore']] = activity
    userinfo.following_lectures[activity['valore']] = lectures

    await query.edit_message_text(
        str(f"Added activity {activity['nome_insegnamento']} events in your google calendar")
    )

    # we can delete the data stored for the query, because we've replaced the buttons
    context.drop_callback_data(query)


async def sync_google(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userinfo = context.user_data["userinfo"]
    update_lectures_to_calendar(userinfo)

async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informs the user that the button is no longer available."""
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Sorry, I could not process this button click 😕 Please send /start to get a new keyboard."
    )


async def google_link_account(update, context):
    flow, auth_url = start_flow()
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

    flow = end_flow(flow, update.message.text)
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
    userinfo = context.user_data["userinfo"]
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

    service = getService(userinfo.credentials)
    calendar = addCalendar(service, "timetable_bot")
    userinfo.has_calendar = True
    userinfo.calendar_id = calendar['id']
    await update.message.reply_text(
        "I successfuly created calendar on your google account\n" +
        f"calendar ID: {userinfo.calendar_id}"
    )

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

    #TODO: add command to list followed events
    #TODO: add check between activities or courses
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("clear", clear))

    # Unitn commands
    application.add_handler(CommandHandler("follow_course", add_unitn_course))

    # General
    application.add_handler(CommandHandler("list_following_courses", list_following_courses))

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
    application.add_handler(CallbackQueryHandler(list_button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
