import dropbox
import os
import requests
import sys

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

# Function to upload a file to Dropbox
def upload_file_to_dropbox(local_file_path, dropbox_file_path, refresh_token, client_id, client_secret):
    # Refresh the access token
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)

    try:
        with open(local_file_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"✅ Uploaded file to Dropbox: {dropbox_file_path}")
    except Exception as e:
        print(f"❌ Failed to upload file to Dropbox: {e}")

# Entry point for the script
if __name__ == "__main__":
    # Command-line arguments
    # The first script saves boundary_conditions.json into '../downloaded_simulation_files/'
    # So we need to ensure this path is correct relative to where this upload script is run.
    output_file_directory = os.path.join("..", "downloaded_simulation_files")
    output_file_name = "boundary_conditions.json"
    local_file_to_upload = os.path.join(output_file_directory, output_file_name)

    dropbox_folder = "/engineering_simulations_pipeline/outputs" # A suggested Dropbox folder for outputs
    refresh_token = sys.argv[1]                    # Dropbox refresh token
    client_id = sys.argv[2]                        # Dropbox client ID
    client_secret = sys.argv[3]                    # Dropbox client secret

    # Check if the generated output file exists
    if not os.path.exists(local_file_to_upload):
        print(f"❌ Error: The output file '{local_file_to_upload}' was not found. Please ensure the first script ran successfully and generated the file.")
        sys.exit(1)

    dropbox_file_path = f"{dropbox_folder}/{output_file_name}"

    # Call the upload function for the generated file
    upload_file_to_dropbox(local_file_to_upload, dropbox_file_path, refresh_token, client_id, client_secret)

    print(f"✅ The generated file '{output_file_name}' has been uploaded to Dropbox.")



