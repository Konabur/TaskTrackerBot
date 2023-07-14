import pygsheets
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup #upm package(python-telegram-bot)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler #upm package(python-telegram-bot)
import datetime
import os

TOKEN = os.getenv('TOKEN')
MANAGER_ID = os.getenv('MANAGER_ID')
SHEET_URL = os.getenv('SHEET_URL')

credentials_file = 'credentials.json'
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
client = pygsheets.authorize(service_file=credentials_file)

spreadsheet = client.open_by_url(SHEET_URL)
sheet = spreadsheet.sheet1

def send_task_message(context, chat_id, text, task_row):
    keyboard = [[
        InlineKeyboardButton("✅", callback_data=f'done_{task_row}'),
        InlineKeyboardButton("❌", callback_data=f'notdone_{task_row}')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

def button_callback(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    data = query.data

    button_data = data.split('_')
    status = button_data[0]
    task_row = int(button_data[1])

    if status == 'done':
        context.bot.send_message(chat_id=os.getenv('MANAGER_ID'), text='Сотрудник выполнил задание.')
        sheet.update_value(f'H{task_row}', 'выполнено')
    elif status == 'notdone':
        context.bot.send_message(chat_id=os.getenv('MANAGER_ID'), text='Сотрудник не выполнил задание.')
        sheet.update_value(f'H{task_row}', 'не выполнено')

    context.bot.delete_message(chat_id=chat_id, message_id=message_id)

def check_task_status(context):
    tasks = sheet.get_all_records()

    for task_row, task in enumerate(tasks, start=2):
        print(task)
        if not all(list(task.values())[:-1]):
            continue
        username = task['Username']
        start_time = datetime.datetime.strptime(f"{task['Date']} {task['Time']}", "%d.%m.%Y %H:%M:%S")
        answer_time = datetime.timedelta(minutes=int(task['Answer Time']))
        current_time = datetime.datetime.now()

        if task['Status'] == 'отправлено' and current_time - start_time > answer_time:
            context.bot.send_message(chat_id=MANAGER_ID, text=f'Сотрудник @{username} не ответил вовремя.')
            sheet.update_value(f'G{task_row}', 'нет ответа')
        elif not task['Status']:
            send_task_message(context, username, task['Text'], task_row)
            sheet.update_value(f'G{task_row}', 'отправлено')

def start_command(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Привет! Я бот напоминаний.')

def main():
    print('Started!')
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    job_queue = updater.job_queue
    job_queue.run_repeating(check_task_status, interval=60)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
