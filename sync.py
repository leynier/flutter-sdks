import os


def sync() -> None:
    # Sync the latest version
    if check_latest_version():
        print("The latest version is downloaded")
        return
    print(f"Downloading the latest version {get_remote_latest_version()}")
    update_latest_version()
    run_main_with_lastest_version()


def run_main_with_lastest_version() -> None:
    # Run main.py with the latest version
    latest_version = get_remote_latest_version()
    os.system(f"python main.py {latest_version}")


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


# Run the main function
if __name__ == "__main__":
    sync()
