import os
import signal
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
    os.killpg(os.getpgid(process[0].pid), signal.SIGKILL)
    message = 'Error: killed migration: ' + process[1]['src'] + ' to ' + process[1]['target']
    print(message)
    logfile = open(get_log_file_path(process[1]), 'w')
    logfile.write(message)
    logfile.close()


def run_atm(migration):
    cp = get_subprocess(migration)
    logfile = open(get_log_file_path(migration), 'w')
    my_timer = Timer(config.migration_timeout, kill, [(cp, migration)])
    my_timer.start()
    for line in cp.stdout:
        logfile.write(line)
        sys.stdout.write(line)
        if '(\'<\' (code 60))' in line or 'Source events are malformed' in line:
            cp.kill()
            break
    cp.wait()
    my_timer.cancel()


def get_subprocess(migration):
    command = config.atm_root + '/run_AppTestMigrator.sh'
    src_path = config.work_dir + migration['src']
    target_path = config.work_dir + migration['target']
    cp = subprocess.Popen([command, src_path, target_path], universal_newlines=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          cwd=config.atm_root, preexec_fn=os.setsid)
    return cp


def migration_process(migration_df, i):
    row = migration_df.iloc[i]
    prepare_for_migration(row)
    run_atm(row)
    err_exist, test_exist = post_migration(row)
    migration_df.at[i, 'error'] = err_exist
    migration_df.at[i, 'test_exist'] = test_exist
