import os
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
        return False  

    os.makedirs(LOCAL_INPUT_FOLDER, exist_ok=True)

    download_files_from_dropbox(DROPBOX_INPUT_FOLDER, LOCAL_INPUT_FOLDER, REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET, LOG_FILE_PATH)

    if not os.listdir(LOCAL_INPUT_FOLDER):
        print(f"⚠️ Warning: No case files found in {LOCAL_INPUT_FOLDER}. Simulation will be skipped.")
        return False

    print("✅ OpenFOAM case files downloaded successfully!")
    return True

def generate_mesh():
    """Runs mesh generation using OpenFOAM inside Docker with proper container validation."""
    
    print("Generating OpenFOAM mesh in Docker container...")

    if not os.listdir(LOCAL_INPUT_FOLDER):
        print("⚠️ Warning: No case files present. Skipping mesh generation.")
        return

    # Step 1: Start Docker container without interactive mode (Remove `-it`)
    container_id = subprocess.run([
        "docker", "run", "-d", "--rm",
        "-v", f"{os.path.abspath(LOCAL_INPUT_FOLDER)}:/workspace/input",
        "-v", f"{os.path.abspath(LOCAL_OUTPUT_FOLDER)}:/workspace/output",
        "-w", "/workspace/input",
        "opencfd/openfoam-run:2306", "/bin/bash", "-c", "sleep infinity"
    ], capture_output=True, text=True).stdout.strip()

    if not container_id:
        print("⚠️ Error: Failed to start OpenFOAM container.")
        return

    print(f"✅ OpenFOAM container started: {container_id}")

    # Step 2: Verify if the container is still running
    running_check = subprocess.run(["docker", "ps", "--filter", f"id={container_id}", "--format", "{{.ID}}"], capture_output=True, text=True).stdout.strip()
    
    if not running_check:
        print(f"⚠️ Error: Container {container_id} stopped unexpectedly.")
        return

    # Step 3: Run OpenFOAM environment setup inside the container (Remove `-it`)
    subprocess.run(["docker", "exec", container_id, "bash", "-c", "source /opt/openfoam10/etc/bashrc"], check=True)

    # Step 4: Execute mesh generation commands separately (Remove `-it`)
    subprocess.run(["docker", "exec", container_id, "blockMesh"], check=True)
    subprocess.run(["docker", "exec", container_id, "surfaceFeatureExtract"], check=True)
    subprocess.run(["docker", "exec", container_id, "snappyHexMesh", "-overwrite"], check=True)
    subprocess.run(["docker", "exec", container_id, "checkMesh"], check=True)

    # Step 5: Copy generated mesh (`polyMesh`) back to Dropbox output folder (Remove `-it`)
    subprocess.run(["docker", "exec", container_id, "bash", "-c", "cp -r constant/polyMesh /workspace/output/"], check=True)

    # Step 6: Stop the container properly
    subprocess.run(["docker", "stop", container_id], check=True)

    print("✅ Mesh generation completed successfully!")

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
    """Runs OpenFOAM inside a Docker container after mesh generation."""

    print("Running OpenFOAM simulation in Docker...")

    if not os.listdir(LOCAL_INPUT_FOLDER):
        print("⚠️ Warning: No case files present. Skipping OpenFOAM execution.")
        return

    # Start a new container for the simulation (Remove `-it`)
    container_id = subprocess.run([
        "docker", "run", "-d", "--rm",
        "-v", f"{os.path.abspath(LOCAL_INPUT_FOLDER)}:/workspace/input",
        "-v", f"{os.path.abspath(LOCAL_OUTPUT_FOLDER)}:/workspace/output",
        "-w", "/workspace/input",
        "opencfd/openfoam-run:2306", "/bin/bash", "-c", "sleep infinity"
    ], capture_output=True, text=True).stdout.strip()

    if not container_id:
        print("⚠️ Error: Failed to start OpenFOAM container.")
        return

    print(f"✅ OpenFOAM container started for simulation: {container_id}")

    # Source OpenFOAM environment
    subprocess.run(["docker", "exec", container_id, "bash", "-c", "source /opt/openfoam10/etc/bashrc"], check=True)

    # Run the OpenFOAM solver
    subprocess.run(["docker", "exec", container_id, "simpleFoam"], check=True)

    # Stop the container after completion
    subprocess.run(["docker", "stop", container_id], check=True)

    print("✅ OpenFOAM simulation executed successfully!")

if __name__ == "__main__":
    if prepare_openfoam_files():
        generate_mesh()  
        run_openfoam_simulation()
    retrieve_simulation_results()



