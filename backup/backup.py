from pydactyl import PterodactylClient

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

import os.path
import os.environ
import sys
import base64
import json
import urllib.request

SERVER_BACKUP = os.environ['SERVER_BACKUP_FOLDER']
SERVER_ID = os.environ['SERVER_ID']

def files_to_backup(server, drive):
    print('Getting files to backup.')
    gd_files = drive.files().list(pageSize=20, supportsAllDrives=True, includeItemsFromAllDrives=True, fields="files(id, name)", orderBy='name desc').execute().get('files')
    mc_files = server.client.servers.files.list_files(SERVER_ID, SERVER_BACKUP)

    upload = []
    for mc_file in mc_files['data']:
        has = None
        for gd_file in gd_files:
            if gd_file['name'] == mc_file['attributes']['name']:
                has = mc_file
        if has == None:
            upload.append(mc_file)
    return upload

def backup_files(server, drive, upload):
    GD_FOLDER = os.environ['GCP_FOLDER_ID']
    
    for file in upload:
        print('Temporary downloading ', file['attributes']['name'], '(', file['attributes']['size']/1000000, 'MB).')
        url = server.client.servers.files.download_file(SERVER_ID, SERVER_BACKUP + '/' + file['attributes']['name'])
        urllib.request.urlretrieve(url, file['attributes']['name'])

        print('Uploading', file['attributes']['name'], ' to Google Drive.')
        media = MediaFileUpload(file['attributes']['name'], file['attributes']['mimetype'], resumable=True)
        body = {
            "name": file['attributes']['name'],
            "parents": [GD_FOLDER]
        }
        request = drive.files().create(body=body, media_body=media, fields='id')
        response = None
        while response == None:
            status, response = request.next_chunk()
            if status:
                print("Progress:", int(status.progress() * 100))
        os.remove(file['attributes']['name'])
        print('Upload of ', file['attributes']['name'], ' completed.')

def connect_to_pentadactyl():
    SERVER_URL = os.environ['PENTADACTYL_HOST']
    SERVER_API = os.environ['PENTADACTYL_KEY']
    
    print('Credentials to Pentadactyl builded.')
    return PterodactylClient(SERVER_URL, SERVER_API)

def connect_to_google_drive_api():
    SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata']
    GCP_CREDENTIALS = os.environ['GCP_CREDENTIALS']
    
    # Create credentials file for GD API
    if os.path.exists('credentials.json') == False:
        with open('credentials.json', 'x') as credentials:
          credentials.write(base64.b64decode(GCP_CREDENTIALS).decode('utf-8'))
    
    credentials = service_account.Credentials.from_service_account_file('credentials.json').with_scopes(SCOPES)

    print('Credentials to Google Drive API builded.')
    return build('drive', 'v3', credentials=credentials)

def main():
    server = connect_to_pentadactyl()
    drive = connect_to_google_drive_api()
    upload = files_to_backup(server, drive)
    backup_files(server, drive, upload)

if __name__ == "__main__":
    main()


