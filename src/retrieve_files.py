import dropbox
import os
import requests

# Define paths
DROPBOX_INPUT_FOLDER = "/simulations/OpenFOAM/input"
LOCAL_INPUT_FOLDER = "./OpenFOAMInputFiles"
LOG_FILE_PATH = "./download_log.txt"

# Function to refresh the access token
def refresh_access_token(refresh_token, client_id, client_secret):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Failed to refresh access token")

# Function to download geometry.stl from Dropbox
def download_geometry_file(refresh_token, client_id, client_secret):
    """Downloads geometry.stl from Dropbox and saves it locally."""
    
    print("Retrieving geometry.stl from Dropbox...")
    
    # Refresh the access token
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)

    try:
        os.makedirs(LOCAL_INPUT_FOLDER, exist_ok=True)
        
        # Search for geometry.stl in the Dropbox folder
        result = dbx.files_list_folder(DROPBOX_INPUT_FOLDER)
        geometry_file = None

        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.lower() == "geometry.stl":
                geometry_file = entry
                break
        
        if not geometry_file:
            print("⚠️ Warning: geometry.stl not found in Dropbox.")
            return False

        local_path = os.path.join(LOCAL_INPUT_FOLDER, geometry_file.name)
        
        # Download the file
        with open(local_path, "wb") as f:
            metadata, res = dbx.files_download(path=geometry_file.path_lower)
            f.write(res.content)

        print(f"✅ Downloaded geometry.stl to {local_path}")

        # Log success
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"Downloaded geometry.stl to {local_path}\n")

        return True
    
    except dropbox.exceptions.ApiError as err:
        print(f"⚠️ Error downloading geometry.stl: {err}")
        return False

# Run the script
if __name__ == "__main__":
    # Retrieve Dropbox credentials from environment variables
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
    CLIENT_ID = os.getenv("APP_KEY")
    CLIENT_SECRET = os.getenv("APP_SECRET")

    if not all([REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("⚠️ Warning: Missing Dropbox credentials! Ensure secrets are set in GitHub Actions.")
    else:
        download_geometry_file(REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET)



