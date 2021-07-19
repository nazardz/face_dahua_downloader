import os
import time
from logzero import logger


# найти старейшии файл (изображение)
def oldest_file_in_tree(rootfolder, extension=".jpg"):
    return min(
        (os.path.join(dirname, filename)
         for dirname, dirnames, filenames in os.walk(rootfolder)
         for filename in filenames
         if filename.endswith(extension)),
        key=lambda fn: os.stat(fn).st_mtime)


# проверка размера папки
def direcroty_size_check(dir_path, limit):
    gigabyte = (1024 ** 3)
    total_size = 0
    for path, dirs, files in os.walk(dir_path):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.path.getsize(fp)
    return False if total_size >= limit * gigabyte else True


# удаление файлов после х дней
def remove_old_files(rootfolder, days, extension=".jpg"):
    current_time = time.time()
    for dirname, dirnames, filenames in os.walk(rootfolder):
        for filename in filenames:
            if filename.endswith(extension):
                creation_time = os.stat(os.path.join(dirname, filename)).st_mtime
                if (current_time - creation_time) // (24 * 3600) >= days:
                    os.remove(os.path.join(dirname, filename))


# проверка путей сохранения
def path_checker(path_name):
    try:
        if not os.path.exists(path_name):
            logger.info('Создание папки...')
            # print('[I] Создание папки... ')
            os.makedirs(path_name)
            logger.info('Папка создана!')
            # print('[I] Папка создана!')
    except OSError:
        logger.error(f'Ошибка создания папки: {path_name}')
        # print('[E] Ошибка создания папки: {}'.format(path_name))
        return False
    return True
