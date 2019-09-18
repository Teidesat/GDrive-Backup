<img width="300" src="logo.png" align="right" />

# GDrive-Backup
> From TEIDESAT Project and Hyperspace Canarias

## Introduction

GDrive-Backup is an small python application designed to maintain a local backup copy 
of the Google Drive cloud files. 

Files are downloaded into a local backup folder. **Each time the application is re-run
the local backup folder gets incrementally updated with changes**. Old files, deleted or 
modified, are moved into a revisions folder. Google Docs, Google Spreadsheets, 
Google Presentations and other Google files are exported as pdf (files bigger
than ~10MB can't be exported due to a limitation of the Google API).   

The credentials.json file from a Google Cloud Platform project is needed (an empty example 
is provided in `credentials_user.json`) which is used to access the API service.

## Prerequisites

- Python modules `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

## Tools and resources used

- [Google Drive API v3](https://developers.google.com/drive/)