import json
from pathlib import Path

from src.FileTree import FileTree
from src.GDriveAPI import GDriveAPI

# Setting root folder will prevent the backup of indexing orphaned folders and their contents (otherwise set to None)
CONFIG_PATH = Path('../config/config.json')
__VERSION__ = '0.1.0-alpha'


def main():
    print('Version %s' % __VERSION__)

    # Read configuration -----------------------------------------------------------------------------------------------
    try:
        with CONFIG_PATH.open('r') as f:
            config        = json.load(f)
            root_folder   = config.get('root_folder', None)
            backup_dir    = Path(config['backup_dir'])
            credentials   = Path(config['credentials'])
            revisions_dir = Path(config['revisions_dir'])
            tree_pickle   = Path(config['tree_pickle'])
            token_pickle  = Path(config['token_pickle'])
            scopes        = config['scopes']
    except FileNotFoundError as e:
        print('Could not read configuration file at \'%s\'. %s.' % (CONFIG_PATH, e))
        return
    except KeyError as e:
        print('Configuration option %s missing from file at \'%s\'.' % (e, CONFIG_PATH))
        return
    except json.JSONDecodeError:
        print('Configuration file is malformed.')
        return

    # Backup app -------------------------------------------------------------------------------------------------------
    api = GDriveAPI(credentials, token_pickle, scopes)

    print('Retrieving all files. This may take a while ...')
    files = api.retrieve_all_files()

    print('Building file tree ...')
    new_tree = FileTree(files, root_folder)

    print('Loading old tree ...')
    try:
        old_tree = FileTree.loader(tree_pickle)
    except FileNotFoundError:
        old_tree = FileTree()
        print('Tree file not found. If this is the first time executing the backup, this is normal behavior.')

    print('Updating backup ...')
    old_tree.update_dir(new_tree, api, backup_dir, revisions_dir)

    print('Saving new tree for next backup ...')
    FileTree.saver(new_tree, tree_pickle)


if __name__ == '__main__':
    main()
