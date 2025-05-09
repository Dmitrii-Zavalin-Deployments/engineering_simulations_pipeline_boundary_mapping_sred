import os
import sys
import subprocess
from download_dropbox_files import download_files_from_dropbox

# Define paths
DROPBOX_INPUT_FOLDER = "/simulations/OpenFOAM/input"
LOCAL_INPUT_FOLDER = "./OpenFOAMInputFiles"
DROPBOX_OUTPUT_FOLDER = "/simulations/OpenFOAM/output"
LOCAL_OUTPUT_FOLDER = "./OpenFOAMOutputFiles"
LOG_FILE_PATH = "./download_log.txt"

def prepare_openfoam_files():
    """Downloads OpenFOAM case files from Dropbox and prepares them for simulation."""
    
    print("Starting OpenFOAM case file download process...")
    
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
    CLIENT_ID = os.getenv("APP_KEY")
    CLIENT_SECRET = os.getenv("APP_SECRET")

    if not all([REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("⚠️ Warning: Missing Dropbox credentials! Ensure secrets are set in GitHub Actions.")
        return False  # Allow execution to continue but notify the issue

    os.makedirs(LOCAL_INPUT_FOLDER, exist_ok=True)

    download_files_from_dropbox(DROPBOX_INPUT_FOLDER, LOCAL_INPUT_FOLDER, REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET, LOG_FILE_PATH)

    # Check if files were downloaded successfully
    if not os.listdir(LOCAL_INPUT_FOLDER):
        print(f"⚠️ Warning: No case files found in {LOCAL_INPUT_FOLDER}. Simulation will be skipped.")
        return False

    print("✅ OpenFOAM case files downloaded successfully!")
    return True

def retrieve_simulation_results():
    """Retrieves OpenFOAM simulation results from Dropbox."""
    
    print("Retrieving simulation results...")

    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
    CLIENT_ID = os.getenv("APP_KEY")
    CLIENT_SECRET = os.getenv("APP_SECRET")

    if not all([REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("⚠️ Warning: Missing Dropbox credentials! Ensure secrets are set in GitHub Actions.")
        return

    os.makedirs(LOCAL_OUTPUT_FOLDER, exist_ok=True)

    download_files_from_dropbox(DROPBOX_OUTPUT_FOLDER, LOCAL_OUTPUT_FOLDER, REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET, LOG_FILE_PATH)

    print("✅ Simulation results retrieved successfully!")

def run_openfoam_simulation():
    """Runs OpenFOAM inside a Docker container with the downloaded case files."""

    print("Running OpenFOAM simulation in Docker...")

    if not os.listdir(LOCAL_INPUT_FOLDER):
        print("⚠️ Warning: No case files present. Skipping OpenFOAM execution.")
        return

    docker_command = [
        "docker", "run", "--rm",
        "-v", f"{os.path.abspath(LOCAL_INPUT_FOLDER)}:/workspace/input",
        "-v", f"{os.path.abspath(LOCAL_OUTPUT_FOLDER)}:/workspace/output",
        "-w", "/workspace",
        "opencfd/openfoam-run:2306",
        "blockMesh"
    ]

    try:
        subprocess.run(docker_command, check=True)
        print("✅ OpenFOAM simulation executed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Warning: OpenFOAM simulation encountered an issue: {e}")

if __name__ == "__main__":
    if prepare_openfoam_files():
        run_openfoam_simulation()
    retrieve_simulation_results()



