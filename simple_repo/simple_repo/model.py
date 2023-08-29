from functools import cached_property

from flask import Blueprint
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records_resources.records.api import Record
from invenio_records.models import RecordMetadata
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess, AuthenticatedUser
from invenio_records_resources.records.systemfields import IndexField, PIDField
from invenio_records_resources.records.systemfields.pid import PIDFieldContext
from invenio_records_resources.resources import RecordResourceConfig, RecordResource
from invenio_records_resources.services import ServiceConfig, RecordServiceConfig, RecordService, RecordLink
import marshmallow as ma
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer
from invenio_records_resources.services.records.components import DataComponent
from flask import current_app
from werkzeug.local import LocalProxy


class ModelRecordIdProvider(RecordIdProviderV2):
    pid_type = "rec"


class ModelRecord(Record):
    index = IndexField("simple_repo-test-record-v1.0.0")
    model_cls = RecordMetadata
    pid = PIDField(
        provider=ModelRecordIdProvider, context_cls=PIDFieldContext, create=True
    )


class ModelPermissionPolicy(RecordPermissionPolicy):
    can_create = [AuthenticatedUser(), SystemProcess()]
    can_search = [AnyUser(), SystemProcess()]
    can_read = [AnyUser(), SystemProcess()]
    can_update = [AuthenticatedUser(), SystemProcess()]
    can_delete = [AuthenticatedUser(), SystemProcess()]


class ModelSchema(ma.Schema):
    title = ma.fields.String()
    id = ma.fields.String()

    class Meta:
        unknown = ma.INCLUDE


class ModelServiceConfig(RecordServiceConfig):
    record_cls = ModelRecord
    permission_policy_cls = ModelPermissionPolicy
    schema = ModelSchema

    url_prefix = "/simple-records"

    components = [DataComponent]

    @property
    def links_item(self):
        return {
            "self": RecordLink("{+api}%s/{id}" % self.url_prefix),
            "ui": RecordLink("{+ui}%s/{id}" % self.url_prefix),
        }


class ModelService(RecordService):
    pass


class ModelUISerializer(MarshmallowSerializer):
    """UI JSON serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ModelSchema,
            list_schema_cls=BaseListSchema,
            schema_context={"object_key": "ui"},
        )


class ModelResourceConfig(RecordResourceConfig):
    blueprint_name = "simple-repo-record"
    url_prefix = "/simple-records"


class ModelResource(RecordResource):
    pass


class ModelExt:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['model-ext'] = self

    @cached_property
    def service(self):
        return ModelService(config=ModelServiceConfig())

    @cached_property
    def resource(self):
        return ModelResource(
            config=ModelResourceConfig,
            service=self.service
        )


def create_api_api_blueprint(app):
    """Create  blueprint."""
    blueprint = app.extensions['model-ext'].resource.as_blueprint()
    blueprint.record_once(init_create_api_blueprint)
    return blueprint


def init_create_api_blueprint(state):
    """Init app."""
    app = state.app
    ext = app.extensions["model-ext"]

    # register service
    sregistry = app.extensions["invenio-records-resources"].registry
    sregistry.register(ext.service, service_id="model_ext")

    # Register indexer
    if hasattr(ext.service, "indexer"):
        iregistry = app.extensions["invenio-indexer"].registry
        iregistry.register(ext.service.indexer, indexer_id="model_ext")


def create_api_app_blueprint(app):
    """Create -ext blueprint."""
    blueprint = Blueprint("model-ext-ext", __name__, url_prefix="")
    blueprint.record_once(init_create_api_blueprint)
    return blueprint


def _ext_proxy(attr):
    return LocalProxy(lambda: getattr(current_app.extensions["model-ext"], attr))


current_service = _ext_proxy("service")
current_resource = _ext_proxy("resource")