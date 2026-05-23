import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CLIENT_SECRET_FILE = "credenciales.json"
TOKEN_FILE = "token.json"

def autenticar():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            token_b64 = os.environ.get("GOOGLE_TOKEN_B64")
            if token_b64:
                creds = Credentials.from_authorized_user_info(
                    json.loads(base64.b64decode(token_b64)), SCOPES
                )
            else:
                creds_json_b64 = os.environ.get("GOOGLE_CREDENTIALS_B64")
                if creds_json_b64:
                    client_config = json.loads(base64.b64decode(creds_json_b64))
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                else:
                    if os.path.exists(CLIENT_SECRET_FILE):
                        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                    else:
                        raise FileNotFoundError("No se encontró archivo de credenciales")
                flow.run_local_server(port=0)
                creds = flow.credentials

    if creds and not os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds

if __name__ == "__main__":
    autenticar()
    print("token.json generado correctamente")
