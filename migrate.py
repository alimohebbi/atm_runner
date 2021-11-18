import os
import signal
import subprocess
import sys
from threading import Timer

from config import Config
from emulator import start_emulator
from post import post_migration, get_log_file_path
from pre import prepare_for_migration

config = Config()


def write_file(input_text, log_file):
    f = open(log_file, "w")
    f.write(input_text)
    f.close()


def kill(process):
    message = 'Timeout Error: **** Migration is killed ****'
    print(message)
    logfile = process[1]
    logfile.write(message)
    os.killpg(os.getpgid(process[0].pid), signal.SIGKILL)


def run_atm(migration):
    cp = get_subprocess(migration)
    logfile = open(get_log_file_path(migration), 'w')
    migration_timer = Timer(config.migration_timeout, kill, [(cp, logfile)])
    migration_timer.start()
    monitor_lines(cp, logfile)
    cp.wait()
    migration_timer.cancel()
    logfile.close()


def monitor_lines(cp, logfile):
    install_timer = None
    for line in cp.stdout:
        logfile.write(line)
        sys.stdout.write(line)
        if install_timer is not None:
            install_timer.cancel()
            install_timer = None
        if 'Installing APK' in line:
            install_timer = Timer(config.install_timeout, kill, [(cp, logfile)])
            install_timer.start()
        if '(\'<\' (code 60))' in line or 'Source events are malformed' in line:
            cp.kill()
            break


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
