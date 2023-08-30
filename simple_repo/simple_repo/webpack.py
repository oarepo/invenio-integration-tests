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
            },
            dependencies={
                # TODO: only for RDM11 !!!!!
                "react-searchkit": "2.0.2",
                "@semantic-ui-react/css-patch": "^1.0.0",
            },
            aliases={
                "../../theme.config$": "less/theme.config",
                "../../less/site": "less/site",
                "../../less": "less",
                "@translations/invenio_app_rdm/i18next": "translations/oarepo_ui/i18next.js",
                "@templates/custom_fields": "js/custom_fields",
            }
        ),
    },
)
