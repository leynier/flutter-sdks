import os
import sys

from mega import Mega


def sync() -> None:
    mega = get_mega_account()
    version = get_version_from_args()
    if not version:
        if check_latest_version():
            print("The latest version is downloaded")
            return
        print(f"Downloading the latest version {get_remote_latest_version()}")
        update_latest_version()
        version = get_local_latest_version()
    download_files(mega, version)


def check_latest_version() -> bool:
    # Check if the latest version is installed
    local_latest_version = get_local_latest_version()
    remote_latest_version = get_remote_latest_version()
    return local_latest_version == remote_latest_version


def update_latest_version() -> None:
    # Update latest_version.txt
    local_latest_version = get_local_latest_version()
    remote_latest_version = get_remote_latest_version()
    if local_latest_version != remote_latest_version:
        with open("latest_version.txt", "w") as f:
            f.write(remote_latest_version)


def get_local_latest_version() -> str:
    # Get the latest version from latest_version.txt
    with open("latest_version.txt", "r") as f:
        return f.read()


def get_remote_latest_version() -> str:
    # Get the tags of Flutter repo without cloning it
    flutter_repo_url = "https://github.com/flutter/flutter.git"
    tags = os.popen(f"git ls-remote --tags {flutter_repo_url}").read()
    # Get the latest version with format number.number.number
    latest_version = ""
    for tag in tags.split("\t"):
        if tag.startswith("refs/tags/"):
            version = tag.split("\n")[0][10:]
            version_splited = version.split(".")
            if (
                len(version_splited) == 3
                and all([x.isdigit() for x in version_splited])
                and version > latest_version
            ):
                latest_version = version
    return latest_version


def get_version_from_args() -> str | None:
    version = sys.argv[1] if len(sys.argv) > 1 else None
    if version:
        version_splited = version.split(".")
        if len(version_splited) == 3 and all([x.isdigit() for x in version_splited]):
            return version


def get_mega_account() -> Mega:
    email: str | None = None
    password: str | None = None
    if os.path.exists(".env"):
        with open(".env") as f:
            lines = f.readlines()
            email_lines = (line for line in lines if line.startswith("EMAIL="))
            email_line = next(email_lines, None)
            password_lines = (line for line in lines if line.startswith("PASSWORD="))
            password_line = next(password_lines, None)
            if email_line:
                email = email_line.split("=")[1].strip()
            if password_line:
                password = password_line.split("=")[1].strip()
    email = email or os.environ.get("EMAIL")
    password = password or os.environ.get("PASSWORD")
    if not email or not password:
        print("Please provide email and password of your mega account.", end=" ")
        print("You can set them in .env file or as environment variables.")
        sys.exit(1)
    m = Mega()
    m.login(email, password)
    return m


def download_files(mega: Mega, version: str) -> None:
    linux_filename = "linux.tar.xz"
    macos_filename = "macos.zip"
    macos_arm64_filename = "macos_arm64.zip"
    windows_filename = "windows.zip"

    linux_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_{version}-stable.tar.xz"
    macos_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_{version}-stable.zip"
    macos_arm64_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_arm64_{version}-stable.zip"
    windows_url = f"https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_{version}-stable.zip"

    filenames = [linux_filename, macos_filename, macos_arm64_filename, windows_filename]
    urls = [linux_url, macos_url, macos_arm64_url, windows_url]

    os.system("sudo apt install -y wget")

    for filename, url in zip(filenames, urls):
        os.system(f"wget {url} -O {filename}")

    for filename in filenames:
        print(f"Deleting {filename} from Mega if exists.")
        file = mega.find(filename, exclude_deleted=True)
        if not file:
            print(f"File {filename} not found on Mega.")
            continue
        file_link = mega.get_link(file)
        mega.delete_url(file_link)
        print(f"File {filename} deleted from Mega.")

    links: dict[str, str] = {}
    for filename in filenames:
        print(f"Uploading {filename} to Mega.")
        file = mega.upload(filename)
        print(f"File {filename} uploaded to Mega.")
        print(f"Getting link for {filename}.")
        link = mega.get_upload_link(file)
        print(f"Link for {filename} is {link}.")
        links[filename] = link

    print("Updating README.md.")
    with open("README.md") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("- [Linux]"):
                lines[i] = f"- [Linux]({links[linux_filename]})\n"
            elif line.startswith("- [MacOS]"):
                lines[i] = f"- [MacOS]({links[macos_filename]})\n"
            elif line.startswith("- [MacOS (arm64)]"):
                lines[i] = f"- [MacOS (arm64)]({links[macos_arm64_filename]})\n"
            elif line.startswith("- [Windows]"):
                lines[i] = f"- [Windows]({links[windows_filename]})\n"

    with open("README.md", "w") as f:
        f.writelines(lines)
    print("README.md updated.")

    print("Committing changes.")
    os.system("git add README.md")
    os.system("git add latest_version.txt")
    os.system(f"git commit -m 'Add Flutter SDK {version}'")
    os.system("git push")
    print("Changes committed.")


# Run the main function
if __name__ == "__main__":
    sync()
