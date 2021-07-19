import os
from logzero import logger, logfile
import time
from datetime import datetime
import utils.memory_check as mc
import utils.dahua_downloader as downloader
import configparser


# Установка пути к лог-файлу
logfile("local/logfile.log", maxBytes=1000000, backupCount=2)

run = True


# pip freeze > requirements.txt
# получить время в формате камеры дахуа для запроса
def data_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    # получить начальное время
    DATE_FROM = data_now()

    logger.info('Запуск..')

    # параметры
    config = configparser.ConfigParser()
    SETTING_PATH = "local/dahua_face/settings.ini"  # /home/dan/PycharmProjects/face_dahua_downloader/utils/settings.ini
    try:
        config.read(SETTING_PATH)
        PATH = config["Setting"]["PATH"]  # path name
        TIMER = int(config["Setting"]["TIME_INTERVAL"])  # seconds
        LIMIT = float(config["Setting"]["LIMIT"])  # gigabytes: 1 == 1 gb
        REPLACE_SAVING = bool(config["Setting"]["REPLACE_SAVING"])  # remove old files and replace by new
        REMOVE_TIMER = int(config["Setting"]["REMOVE_TIMER"])  # days
        dahua_data = eval(config["Dahua_cams"]["data"])  # dahua settings

    except Exception as e:
        # print('[E]', e)
        logger.warning(f'Проверьте настройки! {SETTING_PATH}')
        # print(f'[W] Проверьте настройки! {SETTING_PATH}')
        run = False

    if run:
        # разовый вывод текста - "Папка перполнена. Освободите место"
        STOP_SAVING_TEXT = True

        # получить начальное время
        time.sleep(1)
        DATE_TO = data_now()

        logger.info('Проверка путей сохранения..')
        # print('[I] Проверка путей сохранения..')
        if mc.path_checker(PATH):
            for camera in dahua_data['camera']:
                mc.path_checker(PATH + '/' + camera['hostname'])

            # бесконечный цикл
            try:
                while True:
                    # если папка не переполнена или включена удаление старых файлов:
                    if mc.direcroty_size_check(PATH, LIMIT) or REPLACE_SAVING:
                        # вывод разового предупреждения = True
                        STOP_SAVING_TEXT = True
                        # для камер в словаре
                        for camera in dahua_data['camera']:
                            dd = downloader.DahuaDownloader(dahua_ip=camera['hostname'],  # адрес
                                                            dahua_login=camera['login'],  # логин
                                                            dahua_password=camera['password'],  # пароль
                                                            date_from=DATE_FROM,  # начальная дата
                                                            date_to=DATE_TO,  # конечная дата
                                                            output_path=PATH + '/' + camera['hostname'],
                                                            # путь сохранения для камеры
                                                            limit=LIMIT)  # лимит памяти папки в гигабайтах
                            # если залогинились на камеру:
                            if dd.login_dahua():
                                # получиьть спсиок изоьражении
                                remote_dahua_file_list = dd.create_file_list()
                                for idx, remote_file in enumerate(remote_dahua_file_list):
                                    # сохранить изображение в папке
                                    output_file_name = dd.download_file(remote_file['file_name'],
                                                                        remote_file['file_length'],
                                                                        idx,
                                                                        len(remote_dahua_file_list),
                                                                        PATH)
                                # завершить сессию на камере
                                dd.close_session()

                    # если папка переполнена:
                    else:
                        # вывод разового предупреждения = False
                        if STOP_SAVING_TEXT:
                            logger.warning(f'{PATH} - Папка перполнена. Освободите место')
                            # print("[W] {} - Папка перполнена. Освободите место".format(PATH))
                            STOP_SAVING_TEXT = False

                    # получение новой даты для запроса с разницой в TIMER секунд
                    DATE_FROM = DATE_TO
                    time.sleep(TIMER)
                    mc.remove_old_files(PATH, REMOVE_TIMER)
                    DATE_TO = data_now()

            except KeyboardInterrupt:
                run = False
                pass
