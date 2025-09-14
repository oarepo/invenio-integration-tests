EXTRA_INVENIO_PACKAGES = {
    "pytest-invenio": "pytest-invenio",
    "citeproc-py-styles": "citeproc-py-styles",
}


def normalize_package_name(name: str) -> str:
    """Normalize package name according to PEP 503."""
    return name.replace("_", "-").lower()


def is_invenio_package(package_name: str) -> bool:
    """Check if a package is an Invenio package."""
    package_name = normalize_package_name(package_name)
    return package_name.startswith("invenio-") or package_name in EXTRA_INVENIO_PACKAGES


def invenio2repo(package_name: str) -> str:
    if package_name in EXTRA_INVENIO_PACKAGES:
        package_name = EXTRA_INVENIO_PACKAGES[package_name]
    return f"https://github.com/inveniosoftware/{package_name}"
