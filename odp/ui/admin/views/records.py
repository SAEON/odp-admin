import json

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.const import ODPCollectionTag, ODPRecordTag, ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import RecordFilterForm, RecordForm, RecordTagEmbargoForm, RecordTagNoteForm, RecordTagQCForm
from odp.ui.base import api
from odp.ui.base.lib import tags, utils
from odp.ui.base.templates import Button, ButtonTheme, create_btn, delete_btn, edit_btn

bp = Blueprint('records', __name__)


@bp.route('/')
@api.view(ODPScope.RECORD_READ)
def index():
    page = request.args.get('page', 1)
    id_q = request.args.get('id_q')
    title_q = request.args.get('title_q')
    collection_ids = request.args.getlist('collection')
    parent_id = request.args.get('parent')

    api_filter = ''
    ui_filter = ''
    if id_q:
        api_filter += f'&identifier_q={id_q}'
        ui_filter += f'&id_q={id_q}'
    if title_q:
        api_filter += f'&title_q={title_q}'
        ui_filter += f'&title_q={title_q}'
    for collection_id in collection_ids:
        api_filter += f'&collection_id={collection_id}'
        ui_filter += f'&collection={collection_id}'
    if parent_id:
        api_filter += f'&parent_id={parent_id}'
        ui_filter += f'&parent={parent_id}'

    filter_form = RecordFilterForm(request.args)
    # utils.populate_collection_choices(filter_form.collection)  # unused

    records = api.get(f'/record/?page={page}{api_filter}')
    catalogs = api.get('/catalog/')

    return render_template(
        'record_index.html',
        records=records,
        filter_=ui_filter,
        filter_form=filter_form,
        buttons=[
            create_btn(scope=ODPScope.RECORD_WRITE),
        ],
        catalog_urls={
            catalog['id']: catalog['url'] for catalog in catalogs['items']
        },
    )


@bp.route('/<id>')
@api.view(ODPScope.RECORD_READ)
def detail(id):
    record = api.get(f'/record/{id}')
    catalog_records = api.get(f'/record/{id}/catalog')
    audit_records = api.get(f'/record/{id}/audit')
    catalogs = api.get('/catalog/')

    nosearch_btn = Button(
        label='No search',
        endpoint='.tag_notsearchable',
        theme=ButtonTheme.warning,
        prompt='Are you sure you want to tag the record as not searchable?',
        object_id=id,
        scope=ODPScope.RECORD_NOSEARCH,
    )
    if notsearchable_tag := tags.get_tag_instance(record, ODPRecordTag.NOTSEARCHABLE):
        nosearch_btn.label = 'Searchable'
        nosearch_btn.endpoint = '.untag_notsearchable'
        nosearch_btn.theme = ButtonTheme.success
        nosearch_btn.prompt = 'Are you sure you want the record to be searchable?'

    retract_btn = Button(
        label='Retract',
        endpoint='.tag_retracted',
        theme=ButtonTheme.danger,
        prompt='Are you sure you want to retract the record from public catalogs?',
        object_id=id,
        scope=ODPScope.RECORD_RETRACT,
    )
    if retracted_tag := tags.get_tag_instance(record, ODPRecordTag.RETRACTED):
        retract_btn.label = 'Un-retract'
        retract_btn.endpoint = '.untag_retracted'
        retract_btn.theme = ButtonTheme.success
        retract_btn.prompt = 'Are you sure you want to cancel the record retraction?'

    return render_template(
        'record_detail.html',
        record=record,
        migrated_tag=tags.get_tag_instance(record, ODPRecordTag.MIGRATED),
        notsearchable_tag=notsearchable_tag,
        collection_notsearchable_tag=tags.get_tag_instance(record, ODPCollectionTag.NOTSEARCHABLE),
        retracted_tag=retracted_tag,
        qc_tags=tags.get_tag_instances(record, ODPRecordTag.QC),
        qc_tag_enabled=ODPScope.RECORD_QC in g.user_permissions,
        embargo_tags=tags.get_tag_instances(record, ODPRecordTag.EMBARGO),
        embargo_tag_enabled=ODPScope.RECORD_EMBARGO in g.user_permissions,
        note_tags=tags.get_tag_instances(record, ODPRecordTag.NOTE),
        note_tag_enabled=ODPScope.RECORD_NOTE in g.user_permissions,
        catalog_records=catalog_records,
        audit_records=audit_records,
        buttons=[
            edit_btn(object_id=id, scope=ODPScope.RECORD_WRITE),
            nosearch_btn,
            retract_btn,
            delete_btn(object_id=id, scope=ODPScope.RECORD_WRITE, prompt_args=(record['doi'] or record['sid'],)),
        ],
        create_btn=create_btn(scope=ODPScope.RECORD_WRITE),
        filter_form=RecordFilterForm(),
        catalog_urls={
            catalog['id']: catalog['url'] for catalog in catalogs['items']
        },
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.RECORD_WRITE)
def create():
    form = RecordForm(request.form)
    utils.populate_collection_choices(form.collection_id, include_none=True)
    utils.populate_metadata_schema_choices(form.schema_id)

    if request.method == 'POST' and form.validate():
        api_route = '/record/'
        if ODPScope.RECORD_ADMIN in g.user_permissions:
            api_route += 'admin/'

        try:
            record = api.post(api_route, dict(
                doi=(doi := form.doi.data) or None,
                sid=(sid := form.sid.data) or None,
                collection_id=form.collection_id.data,
                schema_id=form.schema_id.data,
                metadata=json.loads(form.metadata.data),
            ))
            flash(f'Record {doi or sid} has been created.', category='success')
            return redirect(url_for('.detail', id=record['id']))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('record_edit.html', form=form)


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.RECORD_WRITE)
def edit(id):
    record = api.get(f'/record/{id}')

    form = RecordForm(request.form, data=record)
    utils.populate_collection_choices(form.collection_id)
    utils.populate_metadata_schema_choices(form.schema_id)

    if request.method == 'POST' and form.validate():
        api_route = '/record/'
        if ODPScope.RECORD_ADMIN in g.user_permissions:
            api_route += 'admin/'

        try:
            api.put(api_route + id, dict(
                doi=(doi := form.doi.data) or None,
                sid=(sid := form.sid.data) or None,
                collection_id=form.collection_id.data,
                schema_id=form.schema_id.data,
                metadata=json.loads(form.metadata.data),
            ))
            flash(f'Record {doi or sid} has been updated.', category='success')
            return redirect(url_for('.detail', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('record_edit.html', record=record, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.RECORD_WRITE)
def delete(id):
    api_route = '/record/'
    if ODPScope.RECORD_ADMIN in g.user_permissions:
        api_route += 'admin/'

    api.delete(api_route + id)
    flash(f'Record {id} has been deleted.', category='success')
    return redirect(url_for('.index'))


@bp.route('/<id>/tag/qc', methods=('GET', 'POST'))
@api.view(ODPScope.RECORD_QC)
def tag_qc(id):
    record = api.get(f'/record/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs false boolean field
    if request.method == 'POST':
        form = RecordTagQCForm(request.form)
    else:
        record_tag = tags.get_tag_instance(record, ODPRecordTag.QC, user=True)
        form = RecordTagQCForm(data=record_tag['data'] if record_tag else None)

    if request.method == 'POST' and form.validate():
        try:
            api.post(f'/record/{id}/tag', dict(
                tag_id=ODPRecordTag.QC,
                data={
                    'pass_': form.pass_.data,
                    'comment': form.comment.data,
                },
            ))
            flash(f'{ODPRecordTag.QC} tag has been set.', category='success')
            return redirect(url_for('.detail', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'record_tag_edit.html',
        record=record, form=form, tag_endpoint='.tag_qc',
    )


@bp.route('/<id>/untag/qc/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.RECORD_QC)
def untag_qc(id, tag_instance_id):
    api_route = '/record/'
    if ODPScope.RECORD_ADMIN in g.user_permissions:
        api_route += 'admin/'

    api.delete(f'{api_route}{id}/tag/{tag_instance_id}')
    flash(f'{ODPRecordTag.QC} tag has been removed.', category='success')
    return redirect(url_for('.detail', id=id))


@bp.route('/<id>/tag/note', methods=('GET', 'POST'))
@api.view(ODPScope.RECORD_NOTE)
def tag_note(id):
    record = api.get(f'/record/{id}')

    if request.method == 'POST':
        form = RecordTagNoteForm(request.form)
    else:
        record_tag = tags.get_tag_instance(record, ODPRecordTag.NOTE, user=True)
        form = RecordTagNoteForm(data=record_tag['data'] if record_tag else None)

    if request.method == 'POST' and form.validate():
        try:
            api.post(f'/record/{id}/tag', dict(
                tag_id=ODPRecordTag.NOTE,
                data={
                    'comment': form.comment.data,
                },
            ))
            flash(f'{ODPRecordTag.NOTE} tag has been set.', category='success')
            return redirect(url_for('.detail', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'record_tag_edit.html',
        record=record, form=form, tag_endpoint='.tag_note',
    )


@bp.route('/<id>/untag/note/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.RECORD_NOTE)
def untag_note(id, tag_instance_id):
    api_route = '/record/'
    if ODPScope.RECORD_ADMIN in g.user_permissions:
        api_route += 'admin/'

    api.delete(f'{api_route}{id}/tag/{tag_instance_id}')
    flash(f'{ODPRecordTag.NOTE} tag has been removed.', category='success')
    return redirect(url_for('.detail', id=id))


@bp.route('/<id>/tag/embargo', methods=('GET', 'POST'))
@api.view(ODPScope.RECORD_EMBARGO)
def tag_embargo(id):
    record = api.get(f'/record/{id}')

    if request.method == 'POST':
        form = RecordTagEmbargoForm(request.form)
    else:
        # embargo tag has cardinality 'multi', so this will always be an insert
        form = RecordTagEmbargoForm()

    if request.method == 'POST' and form.validate():
        try:
            api.post(f'/record/{id}/tag', dict(
                tag_id=ODPRecordTag.EMBARGO,
                data={
                    'start': form.start.data.isoformat(),
                    'end': form.end.data.isoformat() if form.end.data else None,
                    'comment': form.comment.data,
                },
            ))
            flash(f'{ODPRecordTag.EMBARGO} tag has been set.', category='success')
            return redirect(url_for('.detail', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'record_tag_edit.html',
        record=record, form=form, tag_endpoint='.tag_embargo',
    )


@bp.route('/<id>/untag/embargo/<tag_instance_id>', methods=('POST',))
@api.view(ODPScope.RECORD_EMBARGO)
def untag_embargo(id, tag_instance_id):
    api_route = '/record/'
    if ODPScope.RECORD_ADMIN in g.user_permissions:
        api_route += 'admin/'

    api.delete(f'{api_route}{id}/tag/{tag_instance_id}')
    flash(f'{ODPRecordTag.EMBARGO} tag has been removed.', category='success')
    return redirect(url_for('.detail', id=id))


@bp.route('/<id>/tag/notsearchable', methods=('POST',))
@api.view(ODPScope.RECORD_NOSEARCH)
def tag_notsearchable(id):
    return tags.tag_singleton(
        'record', id, ODPRecordTag.NOTSEARCHABLE
    )


@bp.route('/<id>/untag/notsearchable', methods=('POST',))
@api.view(ODPScope.RECORD_NOSEARCH)
def untag_notsearchable(id):
    return tags.untag_singleton(
        'record', id, ODPRecordTag.NOTSEARCHABLE
    )


@bp.route('/<id>/tag/retracted', methods=('POST',))
@api.view(ODPScope.RECORD_RETRACT)
def tag_retracted(id):
    return tags.tag_singleton(
        'record', id, ODPRecordTag.RETRACTED
    )


@bp.route('/<id>/untag/retracted', methods=('POST',))
@api.view(ODPScope.RECORD_RETRACT)
def untag_retracted(id):
    return tags.untag_singleton(
        'record', id, ODPRecordTag.RETRACTED
    )


@bp.route('/<id>/catalog/<catalog_id>')
@api.view(ODPScope.RECORD_READ)
def catalog_detail(id, catalog_id):
    catalog_record = api.get(f'/record/{id}/catalog/{catalog_id}')
    return render_template('record_catalog_detail.html', catalog_record=catalog_record)


@bp.route('/<id>/audit/<record_audit_id>')
@api.view(ODPScope.RECORD_READ)
def audit_detail(id, record_audit_id):
    record_audit = api.get(f'/record/{id}/record_audit/{record_audit_id}')
    return render_template('record_audit_detail.html', audit=record_audit)


@bp.route('/<id>/tag_audit/<record_tag_audit_id>')
@api.view(ODPScope.RECORD_READ)
def tag_audit_detail(id, record_tag_audit_id):
    record_tag_audit = api.get(f'/record/{id}/record_tag_audit/{record_tag_audit_id}')
    return render_template('record_tag_audit_detail.html', audit=record_tag_audit)
