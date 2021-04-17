import shutil
import subprocess
import json

from config import Config

config = Config()


def remove_dir(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError as a:
        pass


def remove_subjects(migration):
    src_dir = config.work_dir + migration['src']
    remove_dir(src_dir)
    target_dir = config.work_dir + migration['target']
    remove_dir(target_dir)


def clean_dir(migration):
    cp = subprocess.run([config.clean_file], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(cp.stdout)
    print(cp.stderr)
    remove_subjects(migration)


def copy_subjects(migration):
    src_dir = config.work_dir + '/donor/' + migration['src']
    target_dir = config.work_dir + '/target/' + migration['target']
    shutil.copytree(src_dir, config.work_dir + '/' + migration['src'])
    shutil.copytree(target_dir, config.work_dir + '/' + migration['target'])


def add_config_file(migration):
    file_path = config.work_dir + '/config.json'
    col = list(migration.keys())
    col= list(set(col) - {'error', 'test_exist', 'src', 'target'} )
    conf = dict(migration[col])
    with open(file_path, 'w') as f:
        json.dump(conf, f)


def prepare_for_migration(migration):
    clean_dir(migration)
    copy_subjects(migration)
    add_config_file(migration)
