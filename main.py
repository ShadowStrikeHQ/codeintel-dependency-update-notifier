import argparse
import logging
import subprocess
import json
from packaging import version
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Scans project dependencies and notifies if newer versions are available.")
    parser.add_argument("-r", "--requirements", type=str, help="Path to the requirements.txt file.", default="requirements.txt")
    parser.add_argument("-p", "--project_path", type=str, help="Path to the project directory. Defaults to current directory.", default=".")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--check-security", action="store_true", help="Check for known security vulnerabilities using safety.")
    return parser.parse_args()

def get_installed_packages(project_path):
    """
    Retrieves the list of installed packages within the specified project path using pip.
    Handles potential errors during the pip execution.
    """
    try:
        # Construct the command to list installed packages
        command = ["pip", "list", "--format=json"]
        if project_path != ".":
            command.extend(["--path", project_path])

        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Parse the JSON output from pip list
        installed_packages = json.loads(result.stdout)
        return installed_packages
    except subprocess.CalledProcessError as e:
        logging.error(f"Error listing installed packages: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON output from pip: {e}")
        return None
    except FileNotFoundError:
         logging.error("pip not found. Ensure pip is installed and in your PATH.")
         return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

def get_latest_package_version(package_name):
    """
    Retrieves the latest available version of a package from PyPI using pip.
    Handles potential errors during the pip execution.
    """
    try:
        result = subprocess.run(["pip", "install", f"{package_name}==NonExistentVersion"], capture_output=True, text=True, check=False)
        output = result.stderr
        
        # Extract the latest version from the pip output
        start_index = output.find("(from versions:")
        if start_index == -1:
            logging.warning(f"Could not determine the latest version for {package_name}")
            return None

        start_index += len("(from versions:")
        end_index = output.find(")", start_index)
        if end_index == -1:
            logging.warning(f"Could not determine the latest version for {package_name}")
            return None
        
        versions_str = output[start_index:end_index].strip()
        versions = [v.strip() for v in versions_str.split(",")]
        if not versions:
             logging.warning(f"Could not determine the latest version for {package_name}")
             return None
        
        # Return the last version in the list, assuming pip orders them chronologically
        return versions[-1]

    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting latest version for {package_name}: {e}")
        return None
    except FileNotFoundError:
         logging.error("pip not found. Ensure pip is installed and in your PATH.")
         return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
    

def check_for_updates(installed_packages):
    """
    Compares the installed package versions with the latest available versions and
    identifies packages with potential updates.
    """
    updates_available = []

    if installed_packages is None:
        logging.error("No installed packages found. Exiting.")
        return updates_available

    for package in installed_packages:
        package_name = package['name']
        installed_version = package['version']
        
        latest_version = get_latest_package_version(package_name)

        if latest_version:
            try:
                if version.parse(installed_version) < version.parse(latest_version):
                    updates_available.append({
                        "name": package_name,
                        "installed_version": installed_version,
                        "latest_version": latest_version
                    })
                    logging.info(f"Update available for {package_name}: Installed version {installed_version}, latest version {latest_version}")
            except version.InvalidVersion as e:
                logging.warning(f"Invalid version format for {package_name}: {e}")
        else:
            logging.warning(f"Could not retrieve latest version for {package_name}. Skipping update check.")

    return updates_available

def check_security_vulnerabilities(project_path):
    """
    Checks for known security vulnerabilities in the project's dependencies using the 'safety' tool.
    Requires 'safety' to be installed.
    """
    try:
        command = ["safety", "check", "--full-report"]
        if project_path != ".":
            command.extend(["--project", project_path])

        result = subprocess.run(command, capture_output=True, text=True, check=False) # Don't check=True, handle return codes explicitly
        
        if result.returncode == 0:
            logging.info("No known security vulnerabilities found.")
        elif result.returncode == 1:
            logging.warning("Security vulnerabilities found:")
            logging.warning(result.stdout) # Display the safety output
        else:
             logging.error(f"Safety check failed with return code {result.returncode}: {result.stderr}")

    except FileNotFoundError:
        logging.error("Safety not found. Please install it using: pip install safety")
    except Exception as e:
        logging.error(f"An unexpected error occurred during safety check: {e}")
        
def main():
    """
    Main function to execute the dependency update notifier.
    """
    args = setup_argparse()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Starting dependency update check...")
    
    installed_packages = get_installed_packages(args.project_path)

    if installed_packages:
        updates_available = check_for_updates(installed_packages)

        if updates_available:
            print("Updates available:")
            for update in updates_available:
                print(f"- {update['name']}: Installed version {update['installed_version']}, latest version {update['latest_version']}")
        else:
            print("All dependencies are up to date.")
    else:
        logging.error("Failed to retrieve installed packages. Check logs for details.")

    if args.check_security:
        logging.info("Checking for security vulnerabilities...")
        check_security_vulnerabilities(args.project_path)

    logging.info("Dependency update check complete.")

if __name__ == "__main__":
    main()