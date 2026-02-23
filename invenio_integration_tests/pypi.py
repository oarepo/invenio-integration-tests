import abc
import json
import os
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import override


class PackageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.packages = []
        self.in_link = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.in_link = True

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_link = False

    def handle_data(self, data):
        if self.in_link and data.strip():
            self.packages.append(data.strip())


class BasePyPIClient(abc.ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url
        if self.base_url.endswith("/simple"):
            self.base_url = self.base_url[:-7]
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

    def list_packages(self) -> set[str]:
        import httpx

        response = httpx.get(f"{self.base_url}/simple")
        response.raise_for_status()
        parser = PackageParser()
        parser.feed(response.text)
        return set(x.lower().replace("_", "-") for x in parser.packages)

    def download_package(self, package_name: str, version: str, destination: Path):
        # Download source distribution (sdist)
        subprocess.call(
            [
                "pip",
                "download",
                f"{package_name}=={version}",
                "--disable-pip-version-check",
                "--index-url",
                f"{self.base_url}/simple",
                "--dest",
                str(destination),
                "--no-binary",
                ":all:",
                "--no-deps",
                "--isolated",
                "--no-build-isolation",
                "--ignore-requires-python",
            ]
        )

        # Download binary distribution (wheel)
        subprocess.call(
            [
                "pip",
                "download",
                f"{package_name}=={version}",
                "--disable-pip-version-check",
                "--index-url",
                f"{self.base_url}/simple",
                "--dest",
                str(destination),
                "--only-binary",
                ":all:",
                "--no-deps",
                "--isolated",
                "--no-build-isolation",
                "--ignore-requires-python",
            ]
        )

    def upload_packages(self, package_files: list[Path]):
        if "TWINE_USERNAME" not in os.environ or "TWINE_PASSWORD" not in os.environ:
            raise RuntimeError(
                "TWINE_USERNAME and TWINE_PASSWORD environment variables must be set for uploading packages."
            )
        subprocess.call(
            [
                "twine",
                "upload",
                "--verbose",
                "--repository-url",
                self.base_url,
                *[str(package_file.resolve()) for package_file in package_files],
            ]
        )

    @abc.abstractmethod
    def get_package_versions(self, package_name: str) -> list[str]:
        pass


class PyPIClient(BasePyPIClient):

    @override
    def get_package_versions(self, package_name: str) -> list[str]:
        import httpx

        # PyPI JSON API endpoint
        url = f"{self.base_url}/pypi/{package_name}/json"
        response = httpx.get(url)
        response.raise_for_status()
        data = response.json()

        # Filter out yanked versions
        non_yanked_versions = []
        for version, files in data["releases"].items():
            # A version is considered yanked if all its files are yanked
            # or if it has no files but is marked as yanked
            if files and not all(file.get("yanked", False) for file in files):
                non_yanked_versions.append(version)
            elif not files:
                # Include versions with no files (they might be very old releases)
                non_yanked_versions.append(version)

        return non_yanked_versions


class GitLabPyPIClient(PyPIClient):

    @override
    def get_package_versions(self, package_name: str) -> list[str]:
        versions = subprocess.check_output(
            [
                "pip",
                "index",
                "versions",
                package_name,
                "--pre",
                "--disable-pip-version-check",
                "--json",
                "--ignore-requires-python",
                "--index-url",
                f"{self.base_url}/simple",
            ],
            text=True,
        )
        return json.loads(versions)["versions"]
