from pathlib import Path
from typing import List

from src.GDriveAPI import GMimeTypes


class FileTreeNode(object):

    def __init__(self, gid, name, mime_type, created_time, modified_time,
                 parent=None, export_links=None, last_local_update=None):
        if export_links is None:
            export_links = []
        self.gid = gid
        self.name = name
        self.mime_type = mime_type
        self.created_time = created_time
        self.modified_time = modified_time
        self.last_local_update = last_local_update
        self.export_links = export_links
        self.parent = parent
        self.children = []

    def is_file(self):
        return not self.is_google_folder()

    def is_google_file(self):
        return GMimeTypes.GPREFIX.value in self.mime_type and not self.is_google_folder()

    def is_google_folder(self):
        return self.mime_type == GMimeTypes.GFOLDER.value

    def find_in_list(self, l: List['__class__']):
        for i, item in enumerate(l):
            if self == item:
                return i
        return None

    def get_top_node(self):
        if not self.parent:
            return self
        return self.parent.get_top_node()

    def update_local_modified_time(self, base_dir=Path('.')):
        path = base_dir / self.make_relative_path()
        self.last_local_update = path.stat().st_mtime

    def make_relative_path(self, base_dir=None, google_file_suffix_pdf=True):
        path = Path('')
        current = self.parent
        while current:
            path = Path(current.name) / path
            current = current.parent
        path = path / self.name
        if self.is_google_file() and google_file_suffix_pdf:
            path = path.with_suffix('.pdf')
        if base_dir:
            path = base_dir / path
        return path

    def was_modified_in(self, new):
        assert isinstance(new, FileTreeNode)
        assert self.gid == new.gid
        return self.modified_time != new.modified_time or self.name != new.name

    def was_moved_in(self, new):
        assert isinstance(new, FileTreeNode)
        assert self.gid == new.gid
        return self.parent != new.parent

    def __str__(self):
        return self.name

    def __eq__(self, other):
        assert isinstance(other, FileTreeNode)
        return self.gid == other.gid

    @staticmethod
    def from_json(data):
        # Only first parent is used
        return FileTreeNode(data['id'], data['name'], data['mimeType'], data['createdTime'], data['modifiedTime'],
                            data.get('parents', [None])[0], data.get('exportLinks', None))
