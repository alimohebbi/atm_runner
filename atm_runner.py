import pandas as pd

from config import Config
from migrate import migration_process

config = Config()


def load_migrations():
    return pd.read_csv(config.migration_plan_path)


# def redo_erroneous_migrated():
#     global i, row
#     for i, row in migration_df.iterrows():
#         if row['error'] and not row['test_exist']:
#             migration_process(migration_df, row)
#         migration_df.to_csv(config.migration_plan_path, index=False)


def find_or_create():
    global results
    condition = (results['embedding'] == sm_config['embedding']) & \
                (results['train_set'] == sm_config['train_set']) & \
                (results['algorithm'] == sm_config['algorithm']) & \
                (results['descriptor'] == sm_config['descriptor']) & \
                (results['src'] == sm_config['src']) & \
                (results['target'] == sm_config['target'])

    if len(results.index[condition].tolist()) == 1:
        return results.index[condition].tolist()[0]
    results = results.append(sm_config, ignore_index=True)
    return results.index[[-1]].to_list()[0]


def first_round_migration():
    row_index = find_or_create()
    if results.iloc[row_index]['error'] != '':
        print_exist_message(row_index)
        return
    migration_process(results, row_index)


def print_exist_message(row_index):
    str_row = config_str(row_index)
    print("Already exist: " + str_row)


def config_str(row_index):
    col = list(results.columns)
    col.remove('error')
    col.remove('test_exist')
    conf = dict(results.iloc[row_index][col]).values()
    str_row = '_'.join(conf)
    return str_row


def get_results():
    try:
        return pd.read_csv(config.results)
    except FileNotFoundError:
        columns = ["embedding", "train_set", "algorithm", "descriptor", 'src', 'target', 'error', 'test_exist']
        return pd.DataFrame(columns=columns)



if __name__ == '__main__':
    migration_subjects = load_migrations()
    results = get_results()
    results.fillna('', inplace=True)
    for embedding in config.embedding:
        for train_set in config.train_sets:
            for algorithm in config.algorithm:
                for descriptor in config.descriptors:
                    for i, subjects in migration_subjects.iterrows():
                        sm_config = {'embedding': embedding,
                                     'train_set': train_set,
                                     'algorithm': algorithm,
                                     'descriptor': descriptor,
                                     'src': subjects['src'],
                                     'target': subjects['target'],
                                     'error': '',
                                     'test_exist': ''}
                        first_round_migration()
                        results.to_csv(config.results, index=False)
