from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.client import ODPAPIError
from odp.const import ODPCollectionTag, ODPScope, ODPVocabulary
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

    ready_btn = Button(
        label='Ready',
        endpoint='.tag_ready',
        theme=ButtonTheme.success,
        prompt='Are you sure you want to tag the collection as ready for publication?',
        object_id=id,
        enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions,
    )
    if ready_tag := utils.get_tag_instance(collection, ODPCollectionTag.READY):
        ready_btn.label = 'Un-ready'
        ready_btn.endpoint = '.untag_ready'
        ready_btn.theme = ButtonTheme.warning
        ready_btn.prompt = 'Are you sure you want to remove the ready for publication tag?'

    freeze_btn = Button(
        label='Freeze',
        endpoint='.tag_frozen',
        theme=ButtonTheme.warning,
        prompt='Are you sure you want to freeze the collection?',
        object_id=id,
        enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions,
    )
    if frozen_tag := utils.get_tag_instance(collection, ODPCollectionTag.FROZEN):
        freeze_btn.label = 'Un-freeze'
        freeze_btn.endpoint = '.untag_frozen'
        freeze_btn.theme = ButtonTheme.success
        freeze_btn.prompt = 'Are you sure you want to un-freeze the collection?'

    noindex_btn = Button(
        label='Un-index',
        endpoint='.tag_notindexed',
        theme=ButtonTheme.warning,
        prompt='Are you sure you want to tag the collection as not searchable?',
        object_id=id,
        enabled=ODPScope.COLLECTION_NOINDEX in g.user_permissions,
    )
    if notindexed_tag := utils.get_tag_instance(collection, ODPCollectionTag.NOTINDEXED):
        noindex_btn.label = 'Index'
        noindex_btn.endpoint = '.untag_notindexed'
        noindex_btn.theme = ButtonTheme.success
        noindex_btn.prompt = 'Are you sure you want the collection to be searchable?'

    return render_template(
        'collection_view.html',
        collection=collection,
        ready_tag=ready_tag,
        frozen_tag=frozen_tag,
        notindexed_tag=notindexed_tag,
        infrastructure_tags=utils.get_tag_instances(collection, ODPCollectionTag.INFRASTRUCTURE),
        infrastructure_tag_enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions,
        project_tags=utils.get_tag_instances(collection, ODPCollectionTag.PROJECT),
        project_tag_enabled=ODPScope.COLLECTION_PROJECT in g.user_permissions,
        audit_records=audit_records,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.COLLECTION_ADMIN in g.user_permissions),
            ready_btn,
            freeze_btn,
            noindex_btn,
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


@bp.route('/<id>/tag/ready', methods=('POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def tag_ready(id):
    api.post(f'/collection/{id}/tag', dict(
        tag_id=ODPCollectionTag.READY,
        data={},
    ))
    flash(f'{ODPCollectionTag.READY} tag has been set.', category='success')
    return redirect(url_for('.view', id=id))


@bp.route('/<id>/untag/ready', methods=('POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def untag_ready(id):
    collection = api.get(f'/collection/{id}')
    if ready_tag := utils.get_tag_instance(collection, ODPCollectionTag.READY):
        api.delete(f'/collection/admin/{id}/tag/{ready_tag["id"]}')
        flash(f'{ODPCollectionTag.READY} tag has been removed.', category='success')

    return redirect(url_for('.view', id=id))


@bp.route('/<id>/tag/frozen', methods=('POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def tag_frozen(id):
    api.post(f'/collection/{id}/tag', dict(
        tag_id=ODPCollectionTag.FROZEN,
        data={},
    ))
    flash(f'{ODPCollectionTag.FROZEN} tag has been set.', category='success')
    return redirect(url_for('.view', id=id))


@bp.route('/<id>/untag/frozen', methods=('POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def untag_frozen(id):
    collection = api.get(f'/collection/{id}')
    if frozen_tag := utils.get_tag_instance(collection, ODPCollectionTag.FROZEN):
        api.delete(f'/collection/admin/{id}/tag/{frozen_tag["id"]}')
        flash(f'{ODPCollectionTag.FROZEN} tag has been removed.', category='success')

    return redirect(url_for('.view', id=id))


@bp.route('/<id>/tag/notindexed', methods=('POST',))
@api.view(ODPScope.COLLECTION_NOINDEX)
def tag_notindexed(id):
    api.post(f'/collection/{id}/tag', dict(
        tag_id=ODPCollectionTag.NOTINDEXED,
        data={},
    ))
    flash(f'{ODPCollectionTag.NOTINDEXED} tag has been set.', category='success')
    return redirect(url_for('.view', id=id))


@bp.route('/<id>/untag/notindexed', methods=('POST',))
@api.view(ODPScope.COLLECTION_NOINDEX)
def untag_notindexed(id):
    api_route = '/collection/'
    if ODPScope.COLLECTION_ADMIN in g.user_permissions:
        api_route += 'admin/'

    collection = api.get(f'/collection/{id}')
    if notindexed_tag := utils.get_tag_instance(collection, ODPCollectionTag.NOTINDEXED):
        api.delete(f'{api_route}{id}/tag/{notindexed_tag["id"]}')
        flash(f'{ODPCollectionTag.NOTINDEXED} tag has been removed.', category='success')

    return redirect(url_for('.view', id=id))


@bp.route('/<id>/tag/project', methods=('GET', 'POST',))
@api.view(ODPScope.COLLECTION_PROJECT)
def tag_project(id):
    return _tag_vocabulary_term(
        id,
        ODPCollectionTag.PROJECT,
        ODPVocabulary.PROJECT,
        CollectionTagProjectForm,
    )


@bp.route('/<id>/untag/project/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.COLLECTION_PROJECT)
def untag_project(id, tag_instance_id):
    return _untag_vocabulary_term(
        id,
        ODPCollectionTag.PROJECT,
        tag_instance_id,
    )


@bp.route('/<id>/tag/infrastructure', methods=('GET', 'POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def tag_infrastructure(id):
    return _tag_vocabulary_term(
        id,
        ODPCollectionTag.INFRASTRUCTURE,
        ODPVocabulary.INFRASTRUCTURE,
        CollectionTagInfrastructureForm,
    )


@bp.route('/<id>/untag/infrastructure/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.COLLECTION_ADMIN)
def untag_infrastructure(id, tag_instance_id):
    return _untag_vocabulary_term(
        id,
        ODPCollectionTag.INFRASTRUCTURE,
        tag_instance_id,
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


def _tag_vocabulary_term(collection_id, tag_id, vocab_id, form_cls):
    collection = api.get(f'/collection/{collection_id}')
    vocab_field = vocab_id.lower()

    if request.method == 'POST':
        form = form_cls(request.form)
    else:
        # vocabulary tags have cardinality 'multi', so this will
        # always be an insert - i.e. don't populate form for update
        form = form_cls()

    utils.populate_vocabulary_term_choices(form[vocab_field], vocab_id, include_none=True)

    if request.method == 'POST' and form.validate():
        try:
            api.post(f'/collection/{collection_id}/tag', dict(
                tag_id=tag_id,
                data={
                    vocab_field: form[vocab_field].data,
                    'comment': form.comment.data,
                },
            ))
            flash(f'{tag_id} tag has been set.', category='success')
            return redirect(url_for('.view', id=collection_id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(f'collection_tag_{vocab_field}.html', collection=collection, form=form)


def _untag_vocabulary_term(collection_id, tag_id, tag_instance_id):
    api_route = '/collection/'
    if ODPScope.COLLECTION_ADMIN in g.user_permissions:
        api_route += 'admin/'

    api.delete(f'{api_route}{collection_id}/tag/{tag_instance_id}')
    flash(f'{tag_id} tag has been removed.', category='success')
    return redirect(url_for('.view', id=collection_id))
