from pydactyl import PterodactylClient

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

import os
import base64
import urllib.request

SERVER_BACKUP = os.getenv('SERVER_BACKUP_FOLDER')
SERVER_ID = os.getenv('PENTADACTYL_SERVER')

def get_files_list(server, drive):
    print('Listing files.')
    gd_files = drive.files().list(pageSize=20, supportsAllDrives=True, includeItemsFromAllDrives=True, fields="files(id, name)", orderBy='name desc').execute().get('files')
    mc_files = server.client.servers.files.list_files(SERVER_ID, SERVER_BACKUP)
    return mc_files, gd_files

def files_to_backup(mc_files, gd_files):
    print('Getting files to backup.')

    upload = []
    for mc_file in mc_files['data']:
        has = None
        for gd_file in gd_files:
            if gd_file['name'] == mc_file['attributes']['name']:
                has = mc_file
        if has == None:
            upload.append(mc_file)
    return upload

def files_to_delete(mc_files, gd_files):
    print('Getting old files to remove from Google Drive.')
    remove = []
    for gd_file in gd_files:
        has = None
        for mc_file in mc_files:
            if gd_file['name'] == mc_file['attributes']['name']:
                has = mc_file
        if has == None:
            remove.append(gd_file)
    return remove

def remove_old(drive, delete):
    for file in delete:
        try:
            drive.files().delete(file['id']).execute()
            print('File', file['name'], 'deleted from Google Drive.')
        except:
            file = None

def backup_files(server, drive, upload):
    GD_FOLDER = os.getenv('GCP_FOLDER_ID')
    
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
    SERVER_URL = os.getenv('PENTADACTYL_HOST')
    SERVER_API = os.getenv('PENTADACTYL_KEY')
    
    print('Credentials to Pentadactyl builded.')
    return PterodactylClient(SERVER_URL, SERVER_API)

def connect_to_google_drive_api():
    SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata']
    GCP_CREDENTIALS = os.getenv('GCP_CREDENTIALS')
    
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

    mc_files, gd_files = get_files_list(server, drive)

    delete = files_to_delete(mc_files, gd_files)
    remove_old(drive, delete)

    upload = files_to_backup(mc_files, gd_files)
    backup_files(server, drive, upload)

if __name__ == "__main__":
    main()


