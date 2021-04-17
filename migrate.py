import subprocess
import sys
from threading import Timer

from config import Config
from post import post_migration, get_log_file_path
from pre import prepare_for_migration

config = Config()



def write_file(input_text, log_file):
    f = open(log_file, "w")
    f.write(input_text)
    f.close()


def kill(process):
    process[0].kill()
    print('killed')
    print(process[1]['src'] + ' to ' + process[1]['target'])


def run_atm(migration):
    cp = get_subprocess(migration)
    logfile = open(get_log_file_path(migration), 'w')
    my_timer = Timer(config.migration_timeout, kill, [(cp, migration)])
    my_timer.start()
    for line in cp.stdout:
        if '(\'<\' (code 60))' in line:
            cp.kill()
            break
        sys.stdout.write(line)
        logfile.write(line)
    cp.wait()
    my_timer.cancel()


def get_subprocess(migration):
    command = config.atm_root + '/run_AppTestMigrator.sh'
    src_path = config.work_dir + '/' + migration['src']
    target_path = config.work_dir + '/' + migration['target']
    cp = subprocess.Popen([command, src_path, target_path], universal_newlines=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          cwd=config.atm_root)
    return cp


def migration_process(migration_df, i):
    row = migration_df.iloc[i]
    prepare_for_migration(row)
    run_atm(row)
    err_exist, test_exist = post_migration(row)
    migration_df.iloc[i]['error'] = err_exist
    migration_df.iloc[i]['test_exist'] = str(test_exist)
