import io
import pickle
import time
from enum import Enum
from pathlib import Path

from apiclient import errors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class GMimeTypes(Enum):
    GPREFIX       = 'application/vnd.google-apps'
    GDOCS         = 'application/vnd.google-apps.document'
    GDRAWING      = 'application/vnd.google-apps.drawing'
    GFILE         = 'application/vnd.google-apps.file'
    GFOLDER       = 'application/vnd.google-apps.folder'
    GFORM         = 'application/vnd.google-apps.form'
    GFUSIONTABLE  = 'application/vnd.google-apps.fusiontable'
    GMAP          = 'application/vnd.google-apps.map'
    GPRESENTATION = 'application/vnd.google-apps.presentation'
    GSCRIPT       = 'application/vnd.google-apps.script'
    GSITE         = 'application/vnd.google-apps.site'
    GSPREADSHEET  = 'application/vnd.google-apps.spreadsheet'


class GDriveAPI:

    def __init__(self, credentials_path: Path, token_pickle_path: Path, scopes, request_second=10):
        self.__scopes = scopes
        self.__credentials_path = Path(credentials_path)
        self.__token_pickle_path = Path(token_pickle_path)
        self.__time_request = 1.0 / request_second
        self.__last_request = 0
        self.service = self.__build_service()

    def user_info(self):
        return self.__execute_request(self.service.about().get(fields='user'))

    def export_file(self, gid, out_path: Path, mime_type='application/pdf'):
        request = self.service.files().export_media(fileId=gid, mimeType=mime_type)
        self.__execute_download(request, out_path)

    def get_file(self, gid, out_path: Path):
        request = self.service.files().get_media(fileId=gid)
        self.__execute_download(request, out_path)

    def retrieve_all_files(self):
        files = []
        page_token = None
        while True:
            request = self.service.files().list(
                        q="",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType, trashed, createdTime, modifiedTime, parents)',
                        pageToken=page_token
                    )

            response = self.__execute_request(request)
            files += response.get('files', [])
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files

    def __wait_before_request(self):
        wait = self.__time_request - (time.time() - self.__last_request)
        if wait > 0:
            time.sleep(wait)
        self.__last_request = time.time()

    def __execute_request(self, request):
        try:
            self.__wait_before_request()
            return request.execute()
        except errors.HttpError as e:
            print('Error while executing request %s' % e)
            return None

    def __execute_download(self, request, out_path):
        try:
            self.__wait_before_request()
            downloader = MediaIoBaseDownload(io.FileIO(out_path, 'wb'), request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        except errors.HttpError as e:
            print('Error while executing request %s' % e)
            return None

    def __build_service(self):
        credentials = None

        # Try to load from pickle
        if self.__token_pickle_path.exists() and self.__token_pickle_path.is_file():
            with self.__token_pickle_path.open('rb') as f:
                credentials = pickle.load(f)

        # Request credentials if expired or non existent
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.__credentials_path, self.__scopes)
                credentials = flow.run_local_server(port=0)

            with self.__token_pickle_path.open('wb') as f:
                pickle.dump(credentials, f)

        return build('drive', 'v3', credentials=credentials)
