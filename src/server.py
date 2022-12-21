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
from common.methods.unitn_activities import fetch_activities, filter_activities
from src.common.classes.unitn import Attivita, Lezione
from src.common.methods.unitn_schedule import add_lecture_to_calendar, fetch_lectures
from src.common.methods.utils import get_lecture_start_end_timestamps, update_lectures_to_calendar

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
        'Hey'
    )


async def get_activities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    activities_list: list[Attivita] = []
    res = filter_activities(fetch_activities(), query)

    for i in res:
        activities_list.append(i)

    if len(res) == 0:
        await update.message.reply_text("No activities found")
        return

    await update.message.reply_text("Activities found:", reply_markup=build_keyboard_activities(activities_list))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(
        "Use /start to test this bot. Use /clear to clear the stored data so that you can see "
        "what happens, if the button data is not available. "
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears all the user data and access tokens"""
    # TODO
    await update.effective_message.reply_text("All clear!")


def build_keyboard(current_list: List) -> InlineKeyboardMarkup:
    """Helper function to build the next inline keyboard."""
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(str(i), callback_data=(i, current_list))
         for i in current_list]
    )

def build_keyboard_activities(list_attivita: list[Attivita]) -> InlineKeyboardMarkup:
    """Helper function to build the next inline keyboard containing the activities"""
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(i['nome_insegnamento'], callback_data=(i, list_attivita))
         for i in list_attivita]
    )


async def list_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""

    userinfo = context.user_data["userinfo"]

    query = update.callback_query
    await query.answer()
    # Get the data from the callback_data.
    # If you're using a type checker like MyPy, you'll have to use typing.cast
    # to make the checker get the expected type of the callback_data
    activity, list_activities = cast(Tuple[Attivita, list[Attivita]], query.data)

    print(activity)

    lectures : list[Lezione] = fetch_lectures(activity['valore'], True)

    if len(lectures) == 0:
        await query.edit_message_text("No lectures found in the near future")
        return

    userinfo.following_lectures[activity] = lectures

    update_lectures_to_calendar(userinfo)

    await query.edit_message_text(
        str(f"Added activity {activity['nome_insegnamento']} events in your google calendar")
    )

    # we can delete the data stored for the query, because we've replaced the buttons
    context.drop_callback_data(query)


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

async def clear_calendar(update, context):
    userinfo = context.user_data["userinfo"]
    userinfo.calendar_id = None
    userinfo.has_calendar = False
    # context.user_data["userinfo"].flow = None
    # context.user_data["userinfo"].credentials = None
    await update.message.reply_text(
        'Cleared google calendar infos'
    )
    return


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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("activities", get_activities))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("add_google_calendar", add_google_calendar))
    application.add_handler(CommandHandler("clear_calendar", clear_calendar))
    application.add_handler(
        CallbackQueryHandler(handle_invalid_button,
                             pattern=InvalidCallbackData)
    )
    application.add_handler(CallbackQueryHandler(list_button))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("link_google", google_link_account)],
        states={
            link_google_states.INSERT_CODE: [MessageHandler(filters.Regex(".*"), google_get_code)],
        }
        ,
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
