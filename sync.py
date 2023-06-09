import os
import sys

from requests import Response, Session


class PCloud:
    def __init__(self, username: str, password: str) -> None:
        self.__session = Session()
        self.__token = self.__get_token(username, password)

    @staticmethod
    def create_with_env() -> "PCloud":
        username: str | None = None
        password: str | None = None
        if os.path.exists(".env"):
            with open(".env") as f:
                lines = f.readlines()
                username_line = next(
                    (line for line in lines if line.startswith("USERNAME=")),
                    None,
                )
                password_line = next(
                    (line for line in lines if line.startswith("PASSWORD=")),
                    None,
                )
                if username_line:
                    username = username_line.split("=")[1].strip()
                if password_line:
                    password = password_line.split("=")[1].strip()
        username = username or os.environ.get("USERNAME")
        password = password or os.environ.get("PASSWORD")
        if not username or not password:
            print(
                "Please provide username and password of your PCloud account. \n"
                + "You can set them in .env file or as environment variables."
            )
            sys.exit(1)
        return PCloud(username, password)

    @staticmethod
    def ensure_result(response: Response) -> None:
        response.raise_for_status()
        json = response.json()
        if json["result"] != 0:
            raise Exception(f"Error: {json['error']}")

    def __get_token(self, username: str, password: str) -> str:
        response = self.__session.get(
            "https://api.pcloud.com/userinfo",
            params={
                "getauth": 1,
                "logout": 1,
                "username": username,
                "password": password,
            },
        )
        PCloud.ensure_result(response)
        return response.json()["auth"]

    def find_file_id(self, filename) -> int:
        response = self.__session.get(
            "https://api.pcloud.com/listfolder",
            params={
                "auth": self.__token,
                "folderid": 0,
            },
        )
        PCloud.ensure_result(response)
        json = response.json()
        for file in json["metadata"]["contents"]:
            if file["name"] == filename:
                return int(file["fileid"])
        raise Exception(f"File {filename} not found")

    def delete_file(self, filename: str, permanently: bool = False) -> None:
        file_id = self.find_file_id(filename)
        response = self.__session.get(
            "https://api.pcloud.com/deletefile",
            params={
                "auth": self.__token,
                "fileid": file_id,
            },
        )
        PCloud.ensure_result(response)
        if not permanently:
            return
        file_id = int(response.json()["metadata"]["fileid"])
        response = self.__session.get(
            "https://api.pcloud.com/trash_clear",
            params={
                "auth": self.__token,
                "fileid": file_id,
            },
        )
        PCloud.ensure_result(response)

    def upload_file(self, filename: str) -> str:
        response = self.__session.post(
            "https://api.pcloud.com/uploadfile",
            params={
                "auth": self.__token,
                "nopartial": 1,
            },
            files=[(filename, open(filename, "rb"))],
        )
        PCloud.ensure_result(response)
        file_id = [int(file_id) for file_id in response.json()["fileids"]][0]
        response = self.__session.get(
            "https://api.pcloud.com/getfilepublink",
            params={
                "auth": self.__token,
                "fileid": file_id,
            },
        )
        PCloud.ensure_result(response)
        json = response.json()
        code = json["code"]
        return f"https://u.pcloud.link/publink/show?code={code}"


def sync() -> None:
    pcloud = PCloud.create_with_env()
    version = get_version_from_args()
    if not version:
        local_latest_version = get_local_latest_version()
        version = get_remote_latest_version()
        if local_latest_version == version:
            print("The latest version is downloaded")
            return
        print(f"Downloading the latest version {version}")
    download_files(pcloud, version)


def set_local_latest_version(version: str) -> None:
    # Set the latest version in latest_version.txt
    with open("latest_version.txt", "w") as f:
        f.write(version)


def get_local_latest_version() -> str:
    # Get the latest version from latest_version.txt
    with open("latest_version.txt", "r") as f:
        return f.read()


def get_remote_latest_version() -> str:
    # Get the tags of Flutter repo without cloning it
    flutter_repo_url = "https://github.com/flutter/flutter.git"
    tags = os.popen(f"git ls-remote --tags {flutter_repo_url}").read()
    # Get the latest version with format number.number.number
    latest_version = [0, 0, 0]
    for tag in tags.split("\t"):
        if tag.startswith("refs/tags/"):
            version = tag.split("\n")[0][10:]
            version = version.split(".")
            if len(version) != 3:
                continue
            if any((not x.isdigit() for x in version)):
                continue
            version = [int(x) for x in version]
            latest_version = max(latest_version, version)
    return ".".join([str(x) for x in latest_version])


def get_version_from_args() -> str | None:
    version = sys.argv[1] if len(sys.argv) > 1 else None
    if version:
        version_splited = version.split(".")
        if len(version_splited) == 3 and all([x.isdigit() for x in version_splited]):
            return version


def download_files(pcloud: PCloud, version: str) -> None:
    linux_filename = "flutter_sdk_linux.tar.xz"
    macos_filename = "flutter_sdk_macos.zip"
    macos_arm64_filename = "flutter_sdk_macos_arm64.zip"
    windows_filename = "flutter_sdk_windows.zip"

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
        print(f"Deleting {filename} from PCloud if exists.")
        try:
            pcloud.delete_file(filename, permanently=True)
            print(f"File {filename} deleted from PCloud.")
        except:
            print(f"File {filename} not found in PCloud.")

    links: dict[str, str] = {}
    for filename in filenames:
        print(f"Uploading {filename} to PCloud.")
        link = pcloud.upload_file(filename)
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

    set_local_latest_version(version)

    print("Committing changes.")
    os.system("git add README.md")
    os.system("git add latest_version.txt")
    os.system(f"git commit -m 'Add Flutter SDK {version}'")
    os.system("git push")
    print("Changes committed.")


# Run the main function
if __name__ == "__main__":
    sync()
