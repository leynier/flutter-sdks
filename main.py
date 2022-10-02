import os
import sys


def main(version: str) -> None:
    # Create a folder under the sdks folder if not exists
    if not os.path.exists(f"sdks/{version}"):
        os.makedirs(f"sdks/{version}")
    linux_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_{version}-stable.tar.xz"
    macos_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_{version}-stable.zip"
    macos_arm64_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_arm64_{version}-stable.zip"
    windows_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_{version}-stable.zip"
    # Remove the old files if exists
    if os.path.exists(f"sdks/{version}/flutter_linux_{version}-stable.tar.xz"):
        os.remove(f"sdks/{version}/flutter_linux_{version}-stable.tar.xz")
    if os.path.exists(f"sdks/{version}/flutter_macos_{version}-stable.zip"):
        os.remove(f"sdks/{version}/flutter_macos_{version}-stable.zip")
    if os.path.exists(f"sdks/{version}/flutter_macos_arm64_{version}-stable.zip"):
        os.remove(f"sdks/{version}/flutter_macos_arm64_{version}-stable.zip")
    if os.path.exists(f"sdks/{version}/flutter_windows_{version}-stable.zip"):
        os.remove(f"sdks/{version}/flutter_windows_{version}-stable.zip")
    # Install wget without prompt
    os.system("sudo apt install -y wget")
    # Download the files
    os.system(f"wget {linux_url} -P sdks/{version}")
    os.system(f"wget {macos_url} -P sdks/{version}")
    os.system(f"wget {macos_arm64_url} -P sdks/{version}")
    os.system(f"wget {windows_url} -P sdks/{version}")
    # Install git lfs
    os.system("git lfs install")
    # Add download files to git lfs
    os.system(f"git lfs track sdks/{version}/flutter_linux_{version}-stable.tar.xz")
    os.system(f"git lfs track sdks/{version}/flutter_macos_{version}-stable.zip")
    os.system(f"git lfs track sdks/{version}/flutter_macos_arm64_{version}-stable.zip")
    os.system(f"git lfs track sdks/{version}/flutter_windows_{version}-stable.zip")
    # Add the .gitattributes file to git
    os.system("git add .gitattributes")
    # Add the lastest version to git
    os.system("git add latest_version.txt")
    # Add the files to git
    os.system(f"git add sdks/{version}/flutter_linux_{version}-stable.tar.xz")
    os.system(f"git add sdks/{version}/flutter_macos_{version}-stable.zip")
    os.system(f"git add sdks/{version}/flutter_macos_arm64_{version}-stable.zip")
    os.system(f"git add sdks/{version}/flutter_windows_{version}-stable.zip")
    # Commit the changes
    os.system(f"git commit -m 'Add Flutter SDK {version}'")
    # Push the changes
    os.system("git push")


# Run the main function
if __name__ == "__main__":
    # Read the version from the arguments and check if it is valid
    version = sys.argv[1]
    if not version:
        print("Please provide a version")
        sys.exit(1)
    # Run the main function with the version
    main(version)
