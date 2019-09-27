<img width="350" src="logo.png" align="right" />

# GDrive-Backup
[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Google Drive API v3](https://img.shields.io/badge/GDrive%20API-v3-blue.svg)](https://developers.google.com/drive/api/v3/reference?hl=es)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Version](https://img.shields.io/badge/alpha-0.1.1-yellow.svg)

> From TEIDESAT Project and Hyperspace Canarias

## Description

GDrive-Backup is an small python application designed to maintain a local backup copy
of the Google Drive cloud files.

Files are downloaded into a local backup folder. **Each time the application is re-run
the local backup folder gets incrementally updated with changes**. Old files, deleted or
modified, are moved into a revisions folder. Google Docs, Google Spreadsheets,
Google Presentations and other Google files are exported as pdf (files bigger
than ~10MB can't be exported using the API, so they are exported using the export url).   

The credentials.json file from a Google Cloud Platform project is needed (an empty example
is provided in `credentials_user.json`) which is used to access the API service. Change any options
in the configuration file:

```json
{
  "root_folder": "HyperSpace",
  "backup_dir": "../backup",
  "revisions_dir": "../revisions",
  "tree_pickle": "../saves/tree.pickle",
  "token_pickle": "../token/token.pickle",
  "credentials": "../token/credentials_teidesat00.json",
  "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
}
```

Note that modifying the files when the backup update is taking place may result in multiple file errors.

Task scheduler example command for windows: `powershell.exe -windowstyle minimized -c python -u "C:\...\GDrive-Backup\src\run_backup.py" | Tee-Object "../saves/log.txt" -Append`

## Prerequisites

- Python modules `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

## Resources

- [Google Drive API v3](https://developers.google.com/drive/)
