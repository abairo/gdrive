import os.path
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
SCOPES = ["https://www.googleapis.com/auth/drive"]


def authentication() -> dict:
    # TODO fix the return type
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def create_folder(service, folder_name, parent_folder_id=None):
    """Cria uma pasta no Google Drive."""
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")


def get_folder_id(service, folder_name, parent_folder_id=None):
    """Obtém o ID de uma pasta no Google Drive."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get("files", [])
    if items:
        return items[0]["id"]
    return None


def main(filepath: str, folder_id: str):
    creds = authentication()
    try:
        service = build("drive", "v3", credentials=creds)

        # Obtém o caminho relativo do arquivo.
        relative_path = os.path.dirname(filepath)

        # Cria as pastas no Google Drive, se necessário.
        parent_folder_id = folder_id
        if relative_path:
            folders = relative_path.split(os.sep)
            for folder_name in folders:
                folder_id = get_folder_id(service, folder_name, parent_folder_id)
                if not folder_id:
                    parent_folder_id = create_folder(
                        service, folder_name, parent_folder_id
                    )
                else:
                    parent_folder_id = folder_id

        # Cria os metadados do arquivo.
        file_metadata = {
            "name": os.path.basename(filepath),
            "parents": [parent_folder_id],
        }
        media = MediaIoBaseUpload(
            io.FileIO(filepath, "rb"),
            mimetype="application/octet-stream",
            resumable=True,
        )
        # Envia o arquivo.
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(
            f'Arquivo com ID: "{file.get("id")}" foi enviado para o Google Drive com sucesso.'
        )

    except Exception as error:
        print(f"Ocorreu um erro: {error}")


if __name__ == "__main__":
    filepath = "pr/São José dos Pinhais/arquivo.txt"
    folder_id = "1g1cvcyagkRWgv1NT_VjyptdRJA8IgOIE"
    main(filepath, folder_id)
