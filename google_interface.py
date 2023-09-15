# Import the required modules
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from tabulate import tabulate
from tqdm import tqdm
import requests
import pickle
import os
import re

# source for api use: https://www.thepythoncode.com/article/using-google-drive--api-in-python#Download_Files


# Define the scope of access
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
    ]
folder_type = 'application/vnd.google-apps.folder'
mp3_type = 'audio/mpeg'

notes_file_name = 'notes.txt'

# Create a service object for the Google Drive API
def get_drive_service():
    # Load the credentials from the file token.pickle if it exists
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials, let the user log in using the credentials.json file
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # Return the service object for the Google Drive API
    return build('drive', 'v3', credentials=creds)
service = get_drive_service()

def get_files(service):
    files = service.files().list(pageSize=100, fields="nextPageToken, files(id, name, mimeType, size, parents, modifiedTime)").execute()
    files = files.get('files', [])
    return files

def list_files(items):
    if not items:
        print('No files found.')
    else:
        rows = []
        for item in items:
            # get the File ID
            id = item["id"]
            # get the name of file
            name = item["name"]
            try:
                # parent directory ID
                parents = item["parents"][0]
            except:
                # has no parents
                parents = "N/A"
            try:
                # get the size in nice bytes format (KB, MB, etc.)
                size = get_size_format(int(item["size"]))
            except:
                # not a file, may be a folder
                size = "N/A"
            # get the Google Drive type of file
            mime_type = item["mimeType"]
            # get last modified date time
            modified_time = item["modifiedTime"]
            # append everything to the list
            rows.append((id, name, parents, size, mime_type, modified_time))
        return rows

def print_list_files(files):
    print("Files:")
    # convert to a human readable table
    table = tabulate(files, headers=["ID", "Name", "Parents", "Size", "Type", "Modified Time"])
    print(table)

file_ids = {}
def get_final_folders(files):
    global file_ids
    for file in files:
        file_ids[file[0]] = file

    file_structure = {}
    start_id = files[0][2]
    for file in files:
        parent_id = file[2]
        id = file[0]
        if parent_id not in file_structure:
            file_structure[parent_id] = []
        file_structure[parent_id].append(id)
        if id == start_id:
            start_id = parent_id

    final_folders = {}
    for parent_id in file_structure.keys():
        child_ids = file_structure[parent_id]
        no_grandchilds = True
        for id in child_ids:
            if id in file_structure:
                no_grandchilds = False
                break
        if no_grandchilds and child_ids:
            final_folders[parent_id] = child_ids
    return final_folders

# final_folder is the tuple: (folder_id, list of child_ids)
def check_folder(final_folder):
    folder_id = final_folder[0]
    child_ids = final_folder[1]
    num_child_ids = len(child_ids)

    # checking if too many files
    if num_child_ids > 2:
        return False

    child_files = [file_ids[id] for id in child_ids]
    # checking if there is only 1 file and it is the correct type
    if num_child_ids == 1:
        if child_files[0][4] == mp3_type:
            return child_files

    # checking that notes haven't already been written for it
    if child_files[0][1] == notes_file_name or child_files[1][1] == notes_file_name:
        return False

    # checking that both files (there must be 2) are the correct types and returned in correct order
    def both_types_match(child_files):
        if child_files[0][4] == mp3_type:
            if child_files[1][4] == docs_type or child_files[1][4] == docs_type:
                return True

    if both_types_match(child_files):
        return child_files

    # checking reverse order
    reverse_child_files = child_files[::-1]
    if both_types_match(reverse_child_files):
        return reverse_child_files

    return False

def check_folders(final_folders):
    good_folders = [check_folder(final_folder) for final_folder in final_folders.items()]
    good_folders = [folder for folder in good_folders if folder]
    return good_folders

def get_files_to_process():
    # service is automatically made automatically by get_drive_service()
    raw_files = get_files(service)
    files = list_files(raw_files)
    final_folders = get_final_folders(files)
    good_folders = check_folders(final_folders)
    return good_folders

def download_file(file_id, destination):
    service.permissions().create(body={"role": "reader", "type": "anyone"}, fileId=file_id).execute()
    download_file_from_google(file_id, destination)

def download_file_from_google(id, destination):
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    def save_content(response, destination):
        CHUNK_SIZE = 32768

        file_size = int(response.headers.get("Content-Length", 0))
        disposition = response.headers.get("content-disposition")
        filename = re.findall(r'filename="(.+)"', disposition)[0]
        print('file: ', filename, '- size: ', file_size)

        progress = tqdm(response.iter_content(CHUNK_SIZE), f"Downloading {filename}", total=file_size, unit="Byte",  unit_scale=True, unit_divisor=1024)
        with open(destination, 'wb') as file:
            for chunk in progress:
                if chunk:
                    file.write(chunk)
                    progress.update(len(chunk))
        progress.close()

    url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={'id': id}, stream=True)
    print('Downloading', response.url)

    token = get_confirm_token(response)
    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    # download to disk
    save_content(response, destination)


def upload_file(file_name, folder_id, delete_file=False):
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    # upload
    media = MediaFileUpload(file_name, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print("File created, id:", file.get("id"))

    if delete_file:
        os.remove(file_name)

if __name__ == '__main__':
    files = list_files(get_files(service))
    print_list_files(files)
    final_folders = get_final_folders(files)

    good_folders = check_folders(final_folders)
    print(good_folders)

    good_folders = get_files_to_process()
    for folder in good_folders:
        print(folder)

    # creating a dict of the files via their ids





'''
# Get the service object
service = get_drive_service()

# List all the files in the Google Drive account
results = service.files().list(pageSize=100, fields="nextPageToken, files(id, name)").execute()
items = results.get('files', [])

# Print the file names and IDs
if items:
    print('Files:')
    for item in items:
        print(f"{item['name']} ({item['id']})")
else:
    print('No files found.')
    '''


