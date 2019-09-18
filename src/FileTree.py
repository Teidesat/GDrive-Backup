import pickle
import shutil
from datetime import datetime
from pathlib import Path

from src.FileTreeNode import FileTreeNode as Node
from src.utils import recursive_rmdir_parents, file_op_decorator


class FileTree:

    def __init__(self, files=None, root_folder=None):
        if files is None:
            files = []
        self.all_nodes = []
        self.all_files = []
        self.all_folders = []
        self.roots = []
        self.__build(files, root_folder)

    def update_dir(self, new_tree, api, backup_dir, revisions_dir):
        # Calculate diffs
        to_download, to_revision, to_move = FileTree.diff(old_files=self.all_files, new_files=new_tree.all_files)

        # Make base directories
        revision_dir = revisions_dir / Path(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        backup_dir.mkdir(exist_ok=True)
        revisions_dir.mkdir(exist_ok=True)
        if to_revision:
            revision_dir.mkdir()

        # Check that current backup state is consistent
        missing, modified = self.__check_backup_consistency(backup_dir)
        to_download.extend(missing)
        to_download.extend(modified)
        to_revision.extend(modified)

        # Print stats
        print('- Elements in old tree (+dirs):  ', len(self.all_nodes))
        print('- Elements in new tree (+dirs):  ', len(new_tree.files))
        print('- Elements to download:          ', len(to_download))
        print('- Elements to delete (revision): ', len(to_revision))
        print('- Elements moved not modified:   ', len(to_move))

        # Update local backup
        FileTree.revise_files(backup_dir, revision_dir, to_revision)
        FileTree.move_files(backup_dir, to_move)
        FileTree.download_files(api, backup_dir, to_download)

        # Update last modification time for each local file in the new tree
        for file in new_tree.all_files:
            file.update_local_modified_time(backup_dir)

    def __check_backup_consistency(self, base_dir):
        missing = []
        modified = []

        for file in self.all_files:
            path = file.make_relative_path(base_dir)

            if not path.exists():
                print('- File was unexpectedly removed from local backup ! (%s). '
                      'A new copy will be downloaded if any' % path)
                missing.append(file)

            elif path.stat().st_mtime != file.last_local_update:
                print('- File was unexpectedly modified from local backup ! (%s). '
                      'This file will be moved to revision and a new copy will be downloaded if any' % path)
                modified.append(file)

        if not missing and not modified:
            print('- Backup consistency check is ok')

        return missing, modified

    # Static -----------------------------------------------------------------------------------------------------------

    @staticmethod
    def saver(tree, path: Path):
        pickle.dump(tree, path.open('wb'))

    @staticmethod
    def loader(path: Path):
        return pickle.load(path.open('rb'))

    @staticmethod
    def diff(old_files, new_files):
        to_download = []
        to_move     = []
        to_revision = []

        for old_file in old_files:
            # Find matching file in new_files list
            new_file = next((f for f in new_files if f == old_file), None)
            # Check if file was deleted, modified or moved
            was_del = new_file is None
            was_mod = old_file.was_modified_in(new_file) if new_file else False
            was_mov = old_file.was_moved_in(new_file) if new_file else False

            if was_del:
                to_revision.append(old_file)
            elif was_mod:
                to_download.append(new_file)
                to_revision.append(old_file)
            elif was_mov:
                to_move.append((old_file, new_file))

        # Add files that are new
        to_download.extend([f for f in new_files if f not in old_files])
        return to_download, to_revision, to_move

    @staticmethod
    def download_files(api, base_dir, files):
        errors = []
        generator = file_op_decorator(files,
                                      '* Downloading new files. Updates may be slow for large files',
                                      '* Download new files, DONE')
        for file in generator:
            path = file.make_relative_path(base_dir)
            try:
                path.parents[0].mkdir(exist_ok=True, parents=True)
                if file.is_google_file():
                    api.export_file(file.gid, path)
                else:
                    api.get_file(file.gid, path)
            except Exception as e:
                errors.append('%s [%s]' % (path, str(e)))
        for path in errors:
            print('- Error: %s' % path)

    @staticmethod
    def revise_files(base_dir, revision_dir, files):
        errors = []
        generator = file_op_decorator(files, '* Moving deleted files', '* Moving deleted files, DONE')

        for file in generator:
            try:
                FileTree.move_file(origin=file.make_relative_path(base_dir),
                                   destination=revision_dir / Path(file.gid[:5] + '_' + file.name),
                                   remove_parents_until=base_dir)
            except Exception as e:
                errors.append(e)
        for path in errors:
            print('- Error: %s' % path)

    @staticmethod
    def move_files(base_dir, files):
        errors = []
        generator = file_op_decorator(files, '* Moving moved files', '* Moving moved files, DONE')

        for pair in generator:
            try:
                FileTree.move_file(origin=pair[0].make_relative_path(base_dir),
                                   destination=pair[1].make_relative_path(base_dir),
                                   remove_parents_until=base_dir)
            except Exception as e:
                errors.append(e)
        for path in errors:
            print('- Error: %s' % path)

    @staticmethod
    def move_file(origin: Path, destination: Path, remove_parents_until=None):
        if not origin.exists():
            raise '%s [File was not found in the backup]' % origin
        try:
            destination.parents[0].mkdir(exist_ok=True, parents=True)
            shutil.move(str(origin), str(destination))
            if remove_parents_until:
                recursive_rmdir_parents(origin.parents[0], remove_parents_until)
        except Exception as e:
            raise '%s => %s [%s]' % (origin, destination, str(e))

    # Private ----------------------------------------------------------------------------------------------------------

    def __build(self, files, root_folder):
        self.__fill_nodes_and_roots(files)
        self.__build_tree()
        self.__remove_orphan(root_folder)
        self.all_files   = [f for f in self.all_nodes if f.is_google_file()]
        self.all_folders = [f for f in self.all_nodes if f.is_google_folder()]
        print('(%d orphan/trashed files or dirs ignored)' % (len(files) - len(self.all_nodes)))

    def __fill_nodes_and_roots(self, files, ignore_trashed=True):
        # Convert files and folders data (json) into nodes
        self.all_nodes = []
        self.roots = []
        for f in files:
            if not ignore_trashed or not f['trashed']:
                node = Node.from_json(f)
                self.all_nodes.append(node)
                if not node.parent:
                    self.roots.append(node)

    def __build_tree(self):
        # Build the actual tree using node.parent property which contains the immediate parent id
        for file in self.all_nodes:
            file.parent = next((folder for folder in self.all_nodes if file.parent == folder.gid), None)
            if file.parent:
                file.parent.children.append(file)

    def __remove_orphan(self, root_folder):
        # Find nodes that do not belong to the desired root folder if specified
        if root_folder:
            self.all_nodes = [f for f in self.all_nodes if f.get_top_node().name == root_folder]
