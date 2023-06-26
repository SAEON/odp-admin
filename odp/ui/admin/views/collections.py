from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.const import ODPCollectionTag, ODPScope, ODPVocabulary
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import CollectionForm, CollectionTagInfrastructureForm, CollectionTagProjectForm
from odp.ui.admin.views import utils
from odp.ui.base import api
from odp.ui.base.templates import Button, ButtonTheme, create_btn, delete_btn, edit_btn

bp = Blueprint('collections', __name__)


@bp.route('/')
@api.view(ODPScope.COLLECTION_READ)
def index():
    page = request.args.get('page', 1)
    collections = api.get('/collection/', page=page, sort='key')
    return render_template(
        'collection_list.html',
        collections=collections,
        buttons=[
            create_btn(enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.COLLECTION_READ)
def view(id):
    collection = api.get(f'/collection/{id}')
    audit_records = api.get(f'/collection/{id}/audit')

    publish_btn = Button(
        label='Publish',
        endpoint='.tag_published',
        theme=ButtonTheme.success,
        prompt='Are you sure you want to publish the collection?',
        object_id=id,
        enabled=ODPScope.COLLECTION_PUBLISH in g.user_permissions,
    )
    if published_tag := utils.get_tag_instance(collection, ODPCollectionTag.PUBLISHED):
        publish_btn.label = 'Un-publish'
        publish_btn.endpoint = '.untag_published'
        publish_btn.theme = ButtonTheme.warning
        publish_btn.prompt = 'Are you sure you want to un-publish the collection?'

    freeze_btn = Button(
        label='Freeze',
        endpoint='.tag_frozen',
        theme=ButtonTheme.warning,
        prompt='Are you sure you want to freeze the collection?',
        object_id=id,
        enabled=ODPScope.COLLECTION_FREEZE in g.user_permissions,
    )
    if frozen_tag := utils.get_tag_instance(collection, ODPCollectionTag.FROZEN):
        freeze_btn.label = 'Un-freeze'
        freeze_btn.endpoint = '.untag_frozen'
        freeze_btn.theme = ButtonTheme.success
        freeze_btn.prompt = 'Are you sure you want to un-freeze the collection?'

    nosearch_btn = Button(
        label='No search',
        endpoint='.tag_notsearchable',
        theme=ButtonTheme.warning,
        prompt='Are you sure you want to tag the collection as not searchable?',
        object_id=id,
        enabled=ODPScope.COLLECTION_NOSEARCH in g.user_permissions,
    )
    if notsearchable_tag := utils.get_tag_instance(collection, ODPCollectionTag.NOTSEARCHABLE):
        nosearch_btn.label = 'Searchable'
        nosearch_btn.endpoint = '.untag_notsearchable'
        nosearch_btn.theme = ButtonTheme.success
        nosearch_btn.prompt = 'Are you sure you want the collection to be searchable?'

    return render_template(
        'collection_view.html',
        collection=collection,
        published_tag=published_tag,
        frozen_tag=frozen_tag,
        notsearchable_tag=notsearchable_tag,
        harvested_tag=utils.get_tag_instance(collection, ODPCollectionTag.HARVESTED),
        infrastructure_tags=utils.get_tag_instances(collection, ODPCollectionTag.INFRASTRUCTURE),
        infrastructure_tag_enabled=ODPScope.COLLECTION_INFRASTRUCTURE in g.user_permissions,
        project_tags=utils.get_tag_instances(collection, ODPCollectionTag.PROJECT),
        project_tag_enabled=ODPScope.COLLECTION_PROJECT in g.user_permissions,
        audit_records=audit_records,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions),
            publish_btn,
            freeze_btn,
            nosearch_btn,
            delete_btn(object_id=id, enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions, prompt_args=(id,)),
        ],
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.COLLECTION_ADMIN)
def create():
    form = CollectionForm(request.form)
    utils.populate_provider_choices(form.provider_id, include_none=True)

    if request.method == 'POST' and form.validate():
        try:
            collection = api.post('/collection/', dict(
                key=(key := form.key.data),
                name=form.name.data,
                provider_id=form.provider_id.data,
                doi_key=form.doi_key.data or None,
            ))
            flash(f'Collection {key} has been created.', category='success')
            return redirect(url_for('.view', id=collection['id']))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('collection_edit.html', form=form)


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.COLLECTION_ADMIN)
def edit(id):
    collection = api.get(f'/collection/{id}')

    form = CollectionForm(request.form, data=collection)
    utils.populate_provider_choices(form.provider_id)

    if request.method == 'POST' and form.validate():
        try:
            api.put(f'/collection/{id}', dict(
                key=(key := form.key.data),
                name=form.name.data,
                provider_id=form.provider_id.data,
                doi_key=form.doi_key.data or None,
            ))
            flash(f'Collection {key} has been updated.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('collection_edit.html', collection=collection, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def delete(id):
    api.delete(f'/collection/{id}')
    flash(f'Collection {id} has been deleted.', category='success')
    return redirect(url_for('.index'))


@bp.route('/<id>/tag/published', methods=('POST',))
@api.view(ODPScope.COLLECTION_PUBLISH)
def tag_published(id):
    return utils.tag_singleton(
        'collection', id, ODPCollectionTag.PUBLISHED
    )


@bp.route('/<id>/untag/published', methods=('POST',))
@api.view(ODPScope.COLLECTION_PUBLISH)
def untag_published(id):
    return utils.untag_singleton(
        'collection', id, ODPCollectionTag.PUBLISHED
    )


@bp.route('/<id>/tag/frozen', methods=('POST',))
@api.view(ODPScope.COLLECTION_FREEZE)
def tag_frozen(id):
    return utils.tag_singleton(
        'collection', id, ODPCollectionTag.FROZEN
    )


@bp.route('/<id>/untag/frozen', methods=('POST',))
@api.view(ODPScope.COLLECTION_FREEZE)
def untag_frozen(id):
    return utils.untag_singleton(
        'collection', id, ODPCollectionTag.FROZEN
    )


@bp.route('/<id>/tag/notsearchable', methods=('POST',))
@api.view(ODPScope.COLLECTION_NOSEARCH)
def tag_notsearchable(id):
    return utils.tag_singleton(
        'collection', id, ODPCollectionTag.NOTSEARCHABLE
    )


@bp.route('/<id>/untag/notsearchable', methods=('POST',))
@api.view(ODPScope.COLLECTION_NOSEARCH)
def untag_notsearchable(id):
    return utils.untag_singleton(
        'collection', id, ODPCollectionTag.NOTSEARCHABLE
    )


@bp.route('/<id>/tag/project', methods=('GET', 'POST',))
@api.view(ODPScope.COLLECTION_PROJECT)
def tag_project(id):
    return utils.tag_keyword_deprecated(
        'collection', id, ODPCollectionTag.PROJECT, ODPVocabulary.PROJECT, CollectionTagProjectForm
    )


@bp.route('/<id>/untag/project/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.COLLECTION_PROJECT)
def untag_project(id, tag_instance_id):
    return utils.untag_keyword(
        'collection', id, ODPCollectionTag.PROJECT, tag_instance_id
    )


@bp.route('/<id>/tag/infrastructure', methods=('GET', 'POST',))
@api.view(ODPScope.COLLECTION_INFRASTRUCTURE)
def tag_infrastructure(id):
    return utils.tag_keyword_deprecated(
        'collection', id, ODPCollectionTag.INFRASTRUCTURE, ODPVocabulary.INFRASTRUCTURE, CollectionTagInfrastructureForm
    )


@bp.route('/<id>/untag/infrastructure/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.COLLECTION_INFRASTRUCTURE)
def untag_infrastructure(id, tag_instance_id):
    return utils.untag_keyword(
        'collection', id, ODPCollectionTag.INFRASTRUCTURE, tag_instance_id
    )


@bp.route('/<id>/doi/new')
# no @api.view because ajax
def get_new_doi(id):
    try:
        return {'doi': api.get(f'/collection/{id}/doi/new')}
    except ODPAPIError as e:
        return e.error_detail


@bp.route('/<id>/audit/<collection_audit_id>')
@api.view(ODPScope.COLLECTION_READ)
def view_audit_detail(id, collection_audit_id):
    audit_detail = api.get(f'/collection/{id}/collection_audit/{collection_audit_id}')
    return render_template('collection_audit_view.html', audit=audit_detail)


@bp.route('/<id>/tag_audit/<collection_tag_audit_id>')
@api.view(ODPScope.COLLECTION_READ)
def view_tag_audit_detail(id, collection_tag_audit_id):
    audit_detail = api.get(f'/collection/{id}/collection_tag_audit/{collection_tag_audit_id}')
    return render_template('collection_tag_audit_view.html', audit=audit_detail)
