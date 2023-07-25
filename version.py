from typing import Tuple
from zipfile import ZipFile
from github import Github
import json
import shutil
import re
import requests


def check_version(repo, folderPath, versionPath) -> Tuple[bool, str]:
    justNumsRegex = r"v(?P<v>[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2})"
    localVersion = "_"
    repoVersion = "_"

    # Get repo version
    release = repo.get_latest_release()
    repoVersion = release.tag_name

    if not folderPath.exists():
        print("downloading script...")
        return [True, repoVersion]

    # Get local version dets
    localVersionJSON = json.loads(versionPath.read_text(encoding="UTF-8"))

    localVersion = localVersionJSON["version"]

    repoVersionNums = re.match(
        justNumsRegex, repoVersion).group("v").split(".")
    localVersionNums = re.match(
        justNumsRegex, localVersion).group("v").split(".")

    # Version tag always going to be ['0', '0', '0'] at this point
    for i in range(3):
        repoV = int(repoVersionNums[i])
        localV = int(localVersionNums[i])
        if repoV > localV:
            print("updating script...")
            return [True, repoVersion]
        elif repoV < localV:
            return [False, localVersion]

    # TODO: implement comparison checks for beta and dev versions
    return [False, localVersion]


def getVersion(parentDir, packageName) -> str:
    # Checking if program is bundled
    programDir = parentDir / packageName
    versionPath = programDir / "version.json"

    # Setting up github
    g = Github()
    repo = g.get_repo("north-shore-basketball-league/runsheet-script")

    # checking latest version
    updateNeeded, version = check_version(repo, programDir, versionPath)

    # Download new dir
    if updateNeeded:
        if programDir.exists():
            shutil.rmtree(programDir)

        downloadPath = parentDir / f"{version}.zip"

        release = repo.get_release(version)
        downloadAssests = release.assets
        asset = None

        for asset in downloadAssests:
            if asset.content_type == "application/x-zip-compressed":
                asset = asset

        if not asset:
            raise Exception("zip file not found")

        downloadURL = asset.browser_download_url

        res = requests.get(downloadURL)
        downloadPath.open("wb").write(res.content)

        with ZipFile(downloadPath, "r") as zip:
            zip.extractall(programDir)

        with versionPath.open("x", encoding="UTF-8") as f:
            json.dump({"version": version, "type": "stable"}, f)

        downloadPath.unlink()

    return programDir
