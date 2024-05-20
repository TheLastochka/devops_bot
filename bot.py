import logging
import os
# from dotenv import load_dotenv
import re
import paramiko
import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

SSH_HOST = os.getenv("SSH_HOST")

SSH_USERNAME = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
SSH_PORT = os.getenv("SSH_PORT")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

PG_VERSION = os.getenv("PG_VERSION")


if not os.path.exists('./logs'):
    os.makedirs('./logs')
if not os.path.exists('./logs/logfile.txt'):
    with open('./logs/logfile.txt', 'w') as f:
        pass

# Подключаем логирование
logging.basicConfig(
    filename='./logs/logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, encoding='utf-8'
)
# logging.disable(logging.CRITICAL) # Отключаем логирование

logger = logging.getLogger(__name__)


def start(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} запустил бота")
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} запросил помощь")
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} запросил поиск телефонных номеров")
    update.message.reply_text('Введите текст для поиска телефонных номеров')

    return 'find_phone_number'

def findEmailCommand(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} запросил поиск email адресов")
    update.message.reply_text('Введите текст для поиска email адресов')

    return 'find_email'

def verifyPasswordCommand(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} запросил валидацию пароля")
    update.message.reply_text('Введите пароль для валидации')

    return 'verify_password'

def findPhoneNumbers(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} ввел текст для поиска телефонных номеров: {update.message.text}")
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    phoneNumRegex = re.compile(r'(?:8|\+7)[\s\-]?(?:\(\d{3}\)|\d{3})[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')
    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        logger.info(f"Номера телефонов не найдены")
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END# Завершаем выполнение функции
    
    context.user_data['data_type'] = 'phone' # Сохраняем тип данных, которые нашли
    context.user_data['data_to_save'] = phoneNumberList

    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
        
    logger.info(f"Найденные номера телефонов: {phoneNumbers}")
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    # return ConversationHandler.END # Завершаем работу обработчика диалога
    update.message.reply_text('Хотите сохранить найденную информацию? (да/нет)')
    return 'write_to_db'

def findEmail(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} ввел текст для поиска email адресов: {update.message.text}")
    user_input = update.message.text
    emailRegex = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    emailList = emailRegex.findall(user_input) 

    if not emailList:
        logger.info(f"Email не найдены")
        update.message.reply_text('Email не найдены')
        return ConversationHandler.END# Завершаем выполнение функции
    
    context.user_data['data_type'] = 'email'
    context.user_data['data_to_save'] = emailList

    emails = '' 
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' # Записываем очередной
    logger.info(f"Найденные email адреса: {emails}")
    update.message.reply_text(emails) # Отправляем сообщение пользователю
    # return ConversationHandler.END # Завершаем работу обработчика диалога
    update.message.reply_text('Хотите сохранить найденную информацию? (да/нет)')
    return 'write_to_db'

def writeToDB(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} хочет сохранить найденную информацию")
    user_input = update.message.text

    data = context.user_data['data_to_save']
    data_type = context.user_data['data_type']

    context.user_data['data_to_save'] = None
    context.user_data['data_type'] = None

    if user_input.lower() == 'да':
        logger.info(f"Пользователь хочет сохранить информацию")
        if write_psql(data, data_type):
            update.message.reply_text('Информация сохранена')
        else:
            update.message.reply_text('Ошибка сохранения информации')
    elif user_input.lower() == 'нет':
        logger.info(f"Пользователь не хочет сохранить информацию")
        update.message.reply_text('Информация не сохранена')
    else:
        logger.info(f"Пользователь ввел неверные данные")
        update.message.reply_text('Пожалуйста, введите "да" или "нет"')
        return 'write_to_db'

    return ConversationHandler.END

def write_psql(data, data_type):
    success = False
    connection = None
    try:
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = connection.cursor()
        if data_type == 'phone':
            query = "INSERT INTO phones (phone) VALUES (%s)"
            cursor.executemany(query, [(phone,) for phone in data])
        elif data_type == 'email':
            query = "INSERT INTO emails (email) VALUES (%s)"
            cursor.executemany(query, [(email,) for email in data])
        connection.commit()
        success = True
        logger.info("Данные успешно записаны в БД")
    except (Exception, Error) as error:
        logger.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logger.info("Соединение с БД закрыто")
        return success


def verifyPassword(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} ввел пароль для валидации: {update.message.text}")
    user_input = update.message.text

    passwordRegex = re.compile(
        r'^(?=.*[A-Z])'    
        r'(?=.*[a-z])'        
        r'(?=.*\d)'           
        r'(?=.*[!@#$%^&*()?])'  
        r'.{8,}$'              
    )

    if passwordRegex.match(user_input):
        logger.info(f"Пароль сложный")
        update.message.reply_text('Пароль сложный')
    else:
        logger.info(f"Пароль простой")
        update.message.reply_text('Пароль простой')
    
    return ConversationHandler.END


def getAptListCommand(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} запросил список пакетов")
    update.message.reply_text(f"Данная комманда поддерживает два режима.\n1. Вывод всех пакетов.\n2. Поиск информации о введенном пакете.\nВведите номер режима, который вас интересует")
    return 'enter_mode_number'

def enterAptMode(update: Update, context):
    if update.message.text.strip() not in ('1', '2'):
        logger.info(f"{update.effective_user.full_name} введен невалидный режим: {update.message.text}")
        update.message.reply_text(f"Пожалуйста, выберите режим, отправив 1 или 2")
        return 'enter_mode_number'

    logger.debug(f"Выбран режим {update.message.text.strip()}")
    if update.message.text.strip() == '1':
        logger.info(f"Пользователь {update.effective_user.full_name} выбрал режим вывода всех пакетов")
        update.message.reply_text(f"Вы выбрали режим вывода всех пакетов. Подождите немного...")
        data = exec_app_list(None)
        update.message.reply_text(data)
        return ConversationHandler.END

    logger.info(f"Пользователь {update.effective_user.full_name} выбрал режим вывода информации о конкретном пакете")
    update.message.reply_text(f"Вы выбрали режим вывода информации о конкретном пакете")
    update.message.reply_text(f"Введите имя пакета, о котором вы хотите узнать")
    return "get_specific_apt_info"

def getSpecificAptInfo(update: Update, context):
    package_name = update.message.text.strip()
    logger.info(f"Пользователь {update.effective_user.full_name} запросил информацию о пакете {package_name}")
    data = exec_app_list(package_name)
    update.message.reply_text(data)
    return ConversationHandler.END


def exec_app_list(package_name):
    cmd = f'apt show {package_name}'
    if not package_name:
        cmd = 'apt list'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=SSH_HOST, username=SSH_USERNAME, password=SSH_PASSWORD, port=SSH_PORT)
    stdin, stdout, stderr = client.exec_command(cmd)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    if len(data)>3000:
        data = data[:3000]
    return data

map_unix = {
    'get_release': 'lsb_release -a',
    'get_uname': 'uname -a',
    'get_uptime': 'uptime',
    'get_df': 'df -h',
    'get_free': 'free -h',
    'get_mpstat': 'mpstat',
    'get_w': 'w',
    'get_auths': 'journalctl --system -u ssh | grep sshd | tail -n 10',
    'get_critical': 'journalctl --system -p crit | tail -n 5',
    'get_ps': 'ps',
    'get_ss': 'netstat -tulpn',
    'get_services': 'service --status-all | grep +',
}
def get_unix(bot_command):

    if bot_command not in map_unix:
        return 'Unknown command'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=SSH_HOST, username=SSH_USERNAME, password=SSH_PASSWORD, port=SSH_PORT)
    stdin, stdout, stderr = client.exec_command(map_unix[bot_command])
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    if len(data)>3000:
        data = data[:3000]
    return data


map_psql = {
    'get_emails': 'SELECT email FROM emails',
    'get_phone_numbers': 'SELECT phone FROM phones',
}
def get_psql(bot_command):
    if bot_command not in map_psql:
        logger.error("Неизвестная команда")
        return 'Unknown command'
    
    data = 'Error'
    connection = None

    try:
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = connection.cursor()
        cursor.execute(map_psql[bot_command])
        data = cursor.fetchall()
        data = '\n'.join([str(row[0]) for row in data])
        logger.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logger.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logger.info("Соединение с БД закрыто")
        return data

map_repl = {
    # 'get_repl_logs': 'grep repl /bot/db_logs/postgresql-*.log | tail -n 10',
    'get_repl_logs': f'grep repl /var/lib/postgresql/{PG_VERSION}/main/log/postgresql-2024-*.log | tail -n 10',
}
def get_repl(bot_command):
    if bot_command not in map_repl:
        logger.error("Неизвестная команда")
        return 'Unknown command'
    
    cmd = map_repl[bot_command]
    data = os.popen(cmd).read()
    return data


def other_commands(update: Update, context):
    bot_command = update.message.text[1:]
    logger.info(f"Пользователь {update.message.from_user.username}({update.message.from_user.id}) запросил команду {bot_command}")

    if bot_command.startswith('get_'):

        if bot_command in map_repl:
            data = get_repl(bot_command)
            update.message.reply_text(data)
            return

        if bot_command in map_psql:
            data = get_psql(bot_command)
            update.message.reply_text(data)
            return

        if bot_command in map_unix:
            data = get_unix(bot_command)
            update.message.reply_text(data)
            return
        
        update.message.reply_text('Unknown command')
    else:
        update.message.reply_text('Unknown command')

def echo(update: Update, context):
    logger.info(f"Пользователь {update.effective_user.full_name} отправил сообщение: {update.message.text}")
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога телефона
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'write_to_db': [MessageHandler(Filters.text & ~Filters.command, writeToDB)],
        },
        fallbacks=[]
    )

    # Обработчик диалога email
    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'write_to_db': [MessageHandler(Filters.text & ~Filters.command, writeToDB)],
        },
        fallbacks=[]
    )

    # Обработчик диалога email
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'enter_mode_number': [MessageHandler(Filters.text & ~Filters.command, enterAptMode)],
            'get_specific_apt_info': [MessageHandler(Filters.text & ~Filters.command, getSpecificAptInfo)],
        },
        fallbacks=[]
    )

		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerAptList)

    dp.add_handler(MessageHandler(Filters.command, other_commands))

	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
