from datetime import datetime

from wtforms import BooleanField, RadioField, SelectField, StringField, TextAreaField, ValidationError, HiddenField, \
    FieldList, FormField, SelectMultipleField, IntegerField
from wtforms.validators import data_required, input_required, length, optional, regexp, DataRequired

from odp.const import DOI_REGEX, SID_REGEX
from odp.const import ODPMetadataSchema
from odp.const.hydra import GrantType, ResponseType, TokenEndpointAuthMethod
from odp.ui.base.forms import BaseForm, DateStringField, JSONTextField, MultiCheckboxField, StringListField, json_object
from odp.ui.base.forms import SubmissionForm, CreatorForm, ContributorForm


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
    collection_specific = BooleanField(
        label='Collection-specific',
    )
    collection_ids = MultiCheckboxField(
        label='Collections',
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
        validators=[input_required(), json_object],
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


class TagKeywordForm(BaseForm):
    vocabulary = StringField(
        label='Vocabulary',
        render_kw={'readonly': ''},
    )
    keyword = SelectField(
        label='Keyword',
        validators=[input_required()],
    )
    comment = StringField(
        label='Comment',
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
    active = BooleanField(
        label='Active',
    )
    role_ids = MultiCheckboxField(
        label='Roles',
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


class CreatorWithRORForm(CreatorForm):
    ror = StringField(label='ROR')


class ContributorWithRORForm(ContributorForm):
    ror = StringField(label='ROR')


def validate_past_year(form, field):
    current_year = datetime.now().year
    year_val = field.data

    if year_val is None:
        return

    if not (1000 <= year_val <= 9999):
        raise ValidationError('Year must be a 4-digit number (e.g., 2024).')

    if year_val > current_year:
        raise ValidationError(f'Year cannot be in the future.')


class CurationSubmissionForm(SubmissionForm):
    creators = FieldList(
        FormField(CreatorWithRORForm),
        label='Creators',
        min_entries=1,
        description='The main researchers or organisations involved in producing the data submission'
    )
    contributors = FieldList(
        FormField(ContributorWithRORForm),
        label='Contributors',
        min_entries=1,
        description='Other parties who contributed to the resource, including a contact person'
    )
    languages = HiddenField(label='Language', default='en-US')
    publication_year = IntegerField(label='Publication Year', validators=[validate_past_year])
    publisher = SelectField(
        label='Publisher',
        choices=[
            'South African Environmental Observation Network',
            'Department of Forestry, Fisheries and the Environment'
        ])
    format = StringField(label='Format Name')
    resource_type = SelectField('Resource Type', choices=[
        'Audiovisual',
        'Book',
        'BookChapter',
        'Collection',
        'ComputationalNotebook',
        'ConferencePaper',
        'ConferenceProceeding',
        'DataPaper',
        'Dataset',
        'Dissertation',
        'Event',
        'Image',
        'InteractiveResource',
        'Journal',
        'JournalArticle',
        'Model',
        'OutputManagementPlan',
        'PeerReview',
        'PhysicalObject',
        'Preprint',
        'Report',
        'Service',
        'Software',
        'Sound',
        'Standard',
        'Text',
        'Workflow',
        'Other'
    ])
    earth_science_theme_keyword = SelectField(
        'GCMD Earth Science theme keyword',
        choices=[
            'AGRICULTURE',
            'ATMOSPHERE',
            'BIOLOGICAL CLASSIFICATION',
            'BIOSPHERE',
            'CLIMATE INDICATORS',
            'CRYOSPHERE',
            'HUMAN DIMENSIONS',
            'LAND SURFACE',
            'OCEANS',
            'PALEOCLIMATE',
            'SOLID EARTH',
            'SPECTRAL / ENGINEERING',
            'SUN - EARTH INTERACTIONS',
            'TERRESTRIAL HYDROSPHERE'
        ])
    eov_keywords = SelectMultipleField(
        'Essential Ocean Variables (EOVs)',
        choices=[
            "Sea state",
            "Ocean surface stress",
            "Sea ice",
            "Sea surface height",
            "Sea surface temperature, SST",
            "Subsurface temperature",
            "Surface currents",
            "Subsurface currents",
            "Sea surface salinity",
            "Subsurface salinity",
            "Ocean surface heat flux",
            "Ocean bottom pressure",
            "Turbulent diapycnal fluxes (emerging)",
            "Oxygen",
            "Nutrients",
            "Inorganic carbon",
            "Transient tracers",
            "Particulate matter",
            "Nitrous oxide",
            "Stable carbon isotopes",
            "Dissolved organic carbon",
            "Phytoplankton biomass and diversity",
            "Zooplankton biomass and diversity",
            "Fish abundance and distribution",
            "Marine turtles, birds, mammals abundance and distribution",
            "Hard coral cover and composition",
            "Seagrass cover and composition",
            "Macroalgal canopy cover and composition",
            "Mangrove cover and composition",
            "Microbe biomass and diversity (emerging)",
            "Invertebrate abundance and distribution (emerging)"
        ])
    ecv_keywords = SelectMultipleField(
        'ECV Keywords',
        choices=[
            'Precipitation',
            'Surface Pressure',
            'Surface Radiation Budget',
            'Surface Temperature',
            'Surface Water Vapour',
            'Surface Wind Speed and Direction',
            'Upper-air Temperature',
            'Earth Radiation Budget',
            'Lightning',
            'Upper-air Water Vapour',
            'Upper-air Wind Speed and Direction',
            'Clouds',
            'Aerosols',
            'Carbon Dioxide, Methane & Other Greenhouse Gases',
            'Ozone',
            'Precursors for Aerosols and Ozone',
            'Groundwater',
            'Lakes',
            'River Discharge',
            'Terrestrial Water Storage (TWS)',
            'Evaporation from Land',
            'Soil Moisture',
            'Glaciers',
            'Ice sheets and Ice Shelves',
            'Permafrost',
            'Snow',
            'Above-ground Biomass',
            'Albedo',
            'Fire',
            'Fraction of Absorbed Photosynthetically Active Radiation (FAPAR)',
            'Land Cover',
            'Land Surface Temperature',
            'Leaf Area Index',
            'Soil Carbon',
            'Anthropogenic Greenhouse Gas Emissions',
            'Anthropogenic Water Use',
            'Ocean Surface Heat Flux',
            'Sea Ice',
            'Sea Level',
            'Sea State',
            'Surface Currents',
            'Sea Surface Salinity',
            'Surface Stress',
            'Sea Surface Temperature',
            'Subsurface Currents',
            'Subsurface Salinity',
            'Subsurface Temperature',
            'Inorganic Carbon',
            'Nitrous Oxide',
            'Nutrients',
            'Ocean Colour',
            'Oxygen',
            'Transient Tracers',
            'Marine Habitats',
            'Plankton'
        ])


class SubmissionFilterForm(BaseForm):
    status = SelectField(label='Status')


class SubmissionAcceptForm(BaseForm):
    collection_id = SelectField(label='Collection')
    schema_id = RadioField(
        label='Schema',
        choices=[
            ODPMetadataSchema.SAEON_DATACITE4.value,
            ODPMetadataSchema.SAEON_ISO19115.value
        ],
        validators=[data_required()]
    )
