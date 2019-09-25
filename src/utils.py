import time
from pathlib import Path
from typing import List

from FileTreeNode import FileTreeNode


def time_to_str(seconds):
    h = 0
    m = 0
    if seconds > 3600:
        h = int(seconds // 3600)
        seconds -= h * 3600
    if seconds > 60:
        m = int(seconds // 60)
        seconds -= m * 60
    s = int(seconds)
    return '{:02d}h {:02d}m {:02d}s'.format(h, m, s)


def file_op_decorator(files: List[FileTreeNode], progress_msg='Progress', complete_msg='Done'):
    """ Generator that prints progress for a list of files of type FileTreeNode """
    t_begin = time.time()
    remain = 0
    for i, file in enumerate(files):
        print('\r%s... %d/%d [%s] (%s)%s' % (progress_msg, i + 1, len(files), time_to_str(remain), str(file), ' ' * 10), end='')
        yield file
        elapsed = time.time() - t_begin
        average = elapsed / (i + 1)
        remain = average * (len(files) - (i + 1))

    print('\r%s. Took: %s' % (complete_msg, time_to_str(time.time() - t_begin)))


def recursive_rmdir_parents(directory: Path, end=None):
    if end and directory == end:
        return
    if is_empty(directory):
        directory.rmdir()
    if directory.parents:
        recursive_rmdir_parents(directory.parents[0], end)


def is_empty(directory: Path):
    for _ in directory.iterdir():
        return False
    return False
