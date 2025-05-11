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
    """Runs OpenFOAM mesh generation in a headless environment using xvfb-run."""
    
    print("Generating OpenFOAM mesh in Docker container...")

    if not os.listdir(LOCAL_INPUT_FOLDER):
        print("⚠️ Warning: No case files present. Skipping mesh generation.")
        return

    # Step 1: Stop any previous OpenFOAM container to prevent conflicts
    subprocess.run(["docker", "stop", "openfoam_container"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", "openfoam_container"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Step 2: Start a new named Docker container (`openfoam_container`)
    subprocess.run([
        "docker", "run", "-d", "--rm", "--name", "openfoam_container",
        "-v", f"{os.path.abspath(LOCAL_INPUT_FOLDER)}:/workspace/input",
        "-v", f"{os.path.abspath(LOCAL_OUTPUT_FOLDER)}:/workspace/output",
        "-w", "/workspace/input",
        "opencfd/openfoam-run:2306",
        "sleep", "infinity"  # Keeps container running for execution
    ], check=True)

    print("✅ OpenFOAM container started: openfoam_container")

    # Step 3: Verify if the container is running before proceeding
    running_check = subprocess.run(["docker", "ps", "--filter", "name=openfoam_container", "--format", "{{.ID}}"],
                                   capture_output=True, text=True).stdout.strip()
    
    if not running_check:
        print(f"⚠️ Error: OpenFOAM container stopped unexpectedly.")
        return

    # Step 4: Use `xvfb-run` for GUI-dependent OpenFOAM tools
    openfoam_script = """
    source /opt/openfoam10/etc/bashrc
    xvfb-run -a blockMesh
    xvfb-run -a surfaceFeatureExtract
    xvfb-run -a snappyHexMesh -overwrite
    xvfb-run -a checkMesh
    cp -r constant/polyMesh /workspace/output/
    """

    # Step 5: Copy the script into the container and execute it
    with open("openfoam_commands.sh", "w") as script_file:
        script_file.write(openfoam_script)

    subprocess.run(["docker", "cp", "openfoam_commands.sh", "openfoam_container:/workspace/input/openfoam_commands.sh"], check=True)
    subprocess.run(["docker", "exec", "openfoam_container", "bash", "-c", "chmod +x /workspace/input/openfoam_commands.sh && /workspace/input/openfoam_commands.sh"], check=True)

    # Step 6: Stop the container after execution
    subprocess.run(["docker", "stop", "openfoam_container"], check=True)

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

    # Start a new container for the simulation (Using `xvfb-run`)
    subprocess.run([
        "docker", "run", "-d", "--rm", "--name", "openfoam_simulation",
        "-v", f"{os.path.abspath(LOCAL_INPUT_FOLDER)}:/workspace/input",
        "-v", f"{os.path.abspath(LOCAL_OUTPUT_FOLDER)}:/workspace/output",
        "-w", "/workspace/input",
        "opencfd/openfoam-run:2306",
        "sleep", "infinity"
    ], check=True)

    print("✅ OpenFOAM container started for simulation: openfoam_simulation")

    # Source OpenFOAM environment
    subprocess.run(["docker", "exec", "openfoam_simulation", "bash", "-c", "source /opt/openfoam10/etc/bashrc"], check=True)

    # Run the OpenFOAM solver (`simpleFoam`)
    subprocess.run(["docker", "exec", "openfoam_simulation", "xvfb-run", "-a", "simpleFoam"], check=True)

    # Stop the container after completion
    subprocess.run(["docker", "stop", "openfoam_simulation"], check=True)

    print("✅ OpenFOAM simulation executed successfully!")

if __name__ == "__main__":
    if prepare_openfoam_files():
        generate_mesh()  
        run_openfoam_simulation()
    retrieve_simulation_results()



