import ntpath
import os
import pathlib
import re
import shutil

from config import Config
from pre import clean_dir

config = Config()


def config_str(migration):
    col = list(migration.keys())
    col.remove('error')
    col.remove('test_exist')
    col.remove('src')
    col.remove('target')
    conf = dict(migration[col]).values()
    str_row = '_'.join(conf)
    return str_row


def get_log_file_path(migration):
    sub_dir = config_str(migration)
    full_dir = config.migration_log_dir + '/' + sub_dir
    os.makedirs(full_dir, exist_ok=True)
    return full_dir + '/' + migration['src'] + '-' + migration['target'] + '.txt'


def check_log_error(migration):
    file = get_log_file_path(migration)
    with open(file, 'r') as file:
        data = file.read().replace('\n', '')
    return True if ('error' in data) or ('Exception' in data) else False


def is_generated_test_path(file_path):
    file_name = ntpath.basename(file_path)
    pattern = re.compile(".*AppTestMigrator_.*\.java$")
    return pattern.search(str(file_name))


def find_test_file(migration):
    target_path = config.work_dir + migration['target']
    result = None
    for path, sub_dirs, files in os.walk(target_path):
        for name in files:
            file_path = pathlib.PurePath(path, name)
            if is_generated_test_path(file_path):
                result = file_path
                break
    return result


def move_test_file(migration, test_file_path):
    sub_dir = config_str(migration)
    full_dir = config.generated_dir + '/' + sub_dir
    dir_for_migration = full_dir + '/' + migration['src'] + '-' + migration['target']
    os.makedirs(dir_for_migration, exist_ok=True)
    shutil.move(str(test_file_path), dir_for_migration)


def post_migration(migration):
    err_exist = check_log_error(migration)
    test_file_path = find_test_file(migration)
    test_exist = False
    if test_file_path:
        move_test_file(migration, test_file_path)
        test_exist = True
    clean_dir(migration)
    return err_exist, test_exist
