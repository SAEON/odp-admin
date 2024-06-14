from wtforms import BooleanField, FileField, RadioField, SelectField, StringField, TextAreaField, ValidationError
from wtforms.validators import data_required, input_required, length, optional, regexp

from odp.const import DOI_REGEX, ROR_REGEX, SID_REGEX
from odp.const.hydra import GrantType, ResponseType, TokenEndpointAuthMethod
from odp.ui.base.forms import BaseForm
from odp.ui.base.forms.fields import DateStringField, JSONTextField, MultiCheckboxField, StringListField
from odp.ui.base.forms.validators import file_required, json_object


class ClientForm(BaseForm):
    id = StringField(
        label='Client id',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    name = StringField(
        label='Client name',
        validators=[data_required()],
    )
    secret = StringField(
        label='Client secret',
    )
    provider_specific = BooleanField(
        label='Provider-specific',
    )
    provider_id = SelectField(
        label='Provider',
    )
    scope_ids = MultiCheckboxField(
        label='Scope',
    )
    grant_types = MultiCheckboxField(
        label='Grant types',
        choices=[(gt.value, gt.value) for gt in GrantType],
    )
    response_types = MultiCheckboxField(
        label='Response types',
        choices=[(rt.value, rt.value) for rt in ResponseType],
    )
    redirect_uris = StringListField(
        label='Redirect URIs',
    )
    post_logout_redirect_uris = StringListField(
        label='Post-logout redirect URIs',
    )
    client_credentials_grant_access_token_lifespan = StringField(
        label='Access token lifespan (client credentials)',
        description='Leave blank for the system default.',
    )
    token_endpoint_auth_method = RadioField(
        label='Token endpoint auth method',
        choices=[(tm.value, tm.value) for tm in TokenEndpointAuthMethod],
        default=TokenEndpointAuthMethod.CLIENT_SECRET_BASIC.value,
    )
    allowed_cors_origins = StringListField(
        label='Allowed CORS origins',
    )

    def validate_secret(self, field):
        if field.data and len(field.data) < 16:
            raise ValidationError('Client secret must be at least 16 characters long.')

    def validate_scope_ids(self, field):
        if not field.data:
            raise ValidationError('At least one scope must be selected.')


class CollectionForm(BaseForm):
    id = StringField(
        label='Collection id',
        render_kw={'readonly': ''},
    )
    key = StringField(
        label='Collection key',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    name = StringField(
        label='Collection name',
        validators=[data_required()],
    )
    provider_id = SelectField(
        label='Provider',
        validators=[input_required()],
    )
    doi_key = StringField(
        label='DOI key',
    )


class CollectionTagInfrastructureForm(BaseForm):
    infrastructure = SelectField(
        label='Infrastructure id',
        validators=[input_required()],
    )
    comment = StringField(
        label='Comment',
    )


class CollectionTagProjectForm(BaseForm):
    project = SelectField(
        label='Project id',
        validators=[input_required()],
    )
    comment = StringField(
        label='Comment',
    )


class PackageForm(BaseForm):
    title = StringField(
        label='Package title',
        validators=[data_required()],
    )
    provider_id = SelectField(
        label='Provider',
        validators=[input_required()],
    )
    resource_ids = MultiCheckboxField(
        label='Resources',
        dynamic_choices=True,
    )
    notes = TextAreaField(
        label='Notes',
        render_kw={'rows': 5},
    )


class ProviderForm(BaseForm):
    id = StringField(
        label='Provider id',
        render_kw={'readonly': ''},
    )
    key = StringField(
        label='Provider key',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    name = StringField(
        label='Provider name',
        validators=[data_required()],
    )
    user_ids = MultiCheckboxField(
        label='Users',
        dynamic_choices=True,
    )


class RecordForm(BaseForm):
    id = StringField(
        label='Record id',
        render_kw={'readonly': ''},
    )
    doi = StringField(
        label='DOI (Digital Object Identifier)',
        validators=[regexp('^$|' + DOI_REGEX)],
    )
    sid = StringField(
        label='SID (Secondary Identifier)',
        validators=[regexp('^$|' + SID_REGEX)],
    )
    collection_id = SelectField(
        label='Collection',
        validators=[input_required()],
    )
    schema_id = SelectField(
        label='Schema',
        validators=[input_required()],
    )
    metadata = JSONTextField(
        label='Metadata',
        validators=[input_required(), json_object()],
        render_kw={'rows': 24},
    )

    def validate_sid(self, field):
        if not self.doi.data and not field.data:
            raise ValidationError('SID is required if there is no DOI.')


class RecordFilterForm(BaseForm):
    id_q = StringField(
        label='Record ID / DOI / SID',
    )
    title_q = StringField(
        label='Record title',
    )
    collection = MultiCheckboxField(
        label='Filter by collection(s)',
    )


class RecordTagNoteForm(BaseForm):
    comment = TextAreaField(
        label='Note',
    )


class RecordTagQCForm(BaseForm):
    pass_ = BooleanField(
        label='Pass',
    )
    comment = StringField(
        label='Comment',
    )


class RecordTagEmbargoForm(BaseForm):
    start = DateStringField(
        label='Start date',
    )
    end = DateStringField(
        label='End date',
        validators=[optional()],
    )
    comment = StringField(
        label='Comment',
    )

    def validate_end(self, field):
        if self.start.data and field.data and field.data < self.start.data:
            raise ValidationError('The end date cannot be earlier than the start date.')


class ResourceUploadForm(BaseForm):
    provider_id = SelectField(
        label='Provider',
        validators=[input_required()],
    )
    title = StringField(
        label='Resource title',
        validators=[data_required()],
    )
    description = StringField(
        label='Resource description',
    )
    file = FileField(
        label='File upload',
        validators=[file_required()],
    )


class RoleForm(BaseForm):
    id = StringField(
        label='Role id',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    collection_specific = BooleanField(
        label='Collection-specific',
    )
    collection_ids = MultiCheckboxField(
        label='Collections',
    )
    scope_ids = MultiCheckboxField(
        label='Scope',
    )


class UserForm(BaseForm):
    id = StringField(
        label='User id',
        render_kw={'readonly': ''},
    )
    email = StringField(
        label='Email',
        render_kw={'readonly': ''},
    )
    name = StringField(
        label='Name',
        render_kw={'readonly': ''},
    )
    role_ids = MultiCheckboxField(
        label='Roles',
    )
    active = BooleanField(
        label='Active',
    )


class UserFilterForm(BaseForm):
    q = StringField(
        label='Name / Email',
    )
    provider = SelectField(
        label='Provider',
    )
    role = SelectField(
        label='Role',
    )


class VocabularyTermInfrastructureForm(BaseForm):
    id = StringField(
        label='Infrastructure id',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    name = StringField(
        label='Infrastructure name',
        validators=[data_required()],
    )
    description = StringField(
        label='Infrastructure description',
    )


class VocabularyTermInstitutionForm(BaseForm):
    id = StringField(
        label='Institution id',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    title = StringField(
        label='Institution title',
        validators=[data_required()],
    )
    ror = StringField(
        label='ROR (Research Organization Registry) identifier',
        validators=[regexp('^$|' + ROR_REGEX)],
        description='The entire URL i.e. https://ror.org/...'
    )
    url = StringField(
        label='Institution website URL',
    )
    locations = StringListField(
        label='Geographic locations (one per line)',
        render_kw={'rows': 3},
    )


class VocabularyTermProjectForm(BaseForm):
    id = StringField(
        label='Project id',
        filters=[lambda s: s.strip() if s else s],
        validators=[data_required(), length(min=2)],
    )
    title = StringField(
        label='Project title',
        validators=[data_required()],
    )
    description = StringField(
        label='Project description',
    )
