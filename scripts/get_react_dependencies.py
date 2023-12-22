# this file should be called inside a virtualenv containing invenio-app-rdm and invenio-rdm-records
import json

from invenio_app_rdm.theme.webpack import theme as app_theme
from invenio_rdm_records.webpack import theme as rdm_theme

def extract_dependencies(theme):
    themes = {}
    for theme_name, theme_theme in theme.themes.items():
        themes[theme_name] = theme_theme.dependencies
    return themes


def merge_dependencies(*webpacks):
    ret = {}
    for webpack in webpacks:
        for theme_name, theme in extract_dependencies(webpack).items():
            webpack_deps = ret.setdefault(theme_name, {})
            for dependency_name, dependency_values in theme.items():
                webpack_deps.setdefault(dependency_name, {}).update(dependency_values)
    return ret

def main():
    dependencies = merge_dependencies(app_theme, rdm_theme)
    print(json.dumps(dependencies, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()