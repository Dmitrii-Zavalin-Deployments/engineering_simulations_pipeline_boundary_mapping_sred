import dropbox
import os
import requests

# Define paths
DROPBOX_OUTPUT_FOLDER = "/simulations/OpenFOAM/output"
LOCAL_OUTPUT_FOLDER = "./OpenFOAMOutputFiles"
LOG_FILE_PATH = "./upload_log.txt"

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

# Function to upload polyMesh folder to Dropbox
def upload_mesh_to_dropbox(refresh_token, client_id, client_secret):
    """Uploads the polyMesh folder to Dropbox after mesh generation."""
    
    print("Uploading polyMesh to Dropbox...")

    # Refresh the access token
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)

    try:
        if not os.path.exists(LOCAL_OUTPUT_FOLDER):
            print("⚠️ Warning: polyMesh folder does not exist. Skipping upload.")
            return False

        # Iterate through all files in the polyMesh folder
        for root, _, files in os.walk(LOCAL_OUTPUT_FOLDER):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                dropbox_file_path = f"{DROPBOX_OUTPUT_FOLDER}/{file_name}"

                with open(local_file_path, "rb") as f:
                    dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite"))
                
                print(f"✅ Uploaded {file_name} to Dropbox ({dropbox_file_path})")

                # Log success
                with open(LOG_FILE_PATH, "a") as log_file:
                    log_file.write(f"Uploaded {file_name} to {dropbox_file_path}\n")

        print("✅ polyMesh upload completed successfully!")
        return True
    
    except dropbox.exceptions.ApiError as err:
        print(f"⚠️ Error uploading polyMesh: {err}")
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
        upload_mesh_to_dropbox(REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET)



