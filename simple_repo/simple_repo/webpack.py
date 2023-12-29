"""JS/CSS Webpack bundles for Document part of the Czech National Repository."""

from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                # Add your webpack entrypoints
                "integration_tests_search": "./js/search/index.js",
                "integration_tests_form": "./js/form/index.js",


            },
            dependencies={
                "semantic-ui-less": "^2.5.0",
            },
            aliases={
                "../../theme.config$": "less/theme.config",
                "../../less/site": "less/site",
                "../../less": "less",
                "@translations/invenio_app_rdm/i18next": "translations/simple_repo/i18next.js",
                "@translations/invenio_rdm_records/i18next": "translations/simple_repo/i18next.js",
                "@templates/custom_fields": "js/custom_fields",
            }
        ),
    },
)
