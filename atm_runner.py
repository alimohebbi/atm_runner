import pandas as pd

from config import Config
from migrate import migration_process

config = Config()


def load_migrations():
    return pd.read_csv(config.migration_plan_path)


def find_or_create():
    global results
    condition = (results['word_embedding'] == sm_config['word_embedding']) & \
                (results['training_set'] == sm_config['training_set']) & \
                (results['algorithm'] == sm_config['algorithm']) & \
                (results['descriptors'] == sm_config['descriptors']) & \
                (results['src'] == sm_config['src']) & \
                (results['target'] == sm_config['target'])

    if len(results.index[condition].tolist()) == 1:
        return results.index[condition].tolist()[0]
    results = results.append(sm_config, ignore_index=True)
    return results.index[[-1]].to_list()[0]


def forbidden_config(semantic_config):
    if semantic_config['word_embedding'] in ['jaccard', 'edit_distance', 'random']:
        return semantic_config['training_set'] != 'empty'
    if semantic_config['word_embedding'] in ['use', 'nnlm', 'bert']:
        return semantic_config['training_set'] != 'standard'
    if semantic_config['word_embedding'] not in ['jaccard', 'edit_distance', 'random']:
        return semantic_config['training_set'] == 'empty'


def first_round_migration():
    if forbidden_config(sm_config):
        return
    row_index = find_or_create()
    if results.iloc[row_index]['error'] != '':
        print_exist_message(row_index)
        return
    migration_process(results, row_index)


def redo_failed_migaratoins():
    if forbidden_config(sm_config):
        return
    row_index = find_or_create()
    if bool(results.iloc[row_index]['error']) and not results.iloc[row_index]['test_exist']:
        print('Redo the failed migration: ' + config_str(row_index))
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
        columns = ["word_embedding", "training_set", "algorithm", "descriptors", 'src', 'target', 'error', 'test_exist']
        return pd.DataFrame(columns=columns)


if __name__ == '__main__':
    migration_subjects = load_migrations()
    results = get_results()
    results.fillna('', inplace=True)
    for embedding in config.embedding:
        for train_set in config.train_sets:
            for algorithm in config.algorithm:
                for descriptors in config.descriptors:
                    for i, subjects in migration_subjects.iterrows():
                        sm_config = {'word_embedding': embedding,
                                     'training_set': train_set,
                                     'algorithm': algorithm,
                                     'descriptors': descriptors,
                                     'src': subjects['src'],
                                     'target': subjects['target'],
                                     'error': '',
                                     'test_exist': ''}
                        first_round_migration()
                        redo_failed_migaratoins()
                        results.to_csv(config.results, index=False)
