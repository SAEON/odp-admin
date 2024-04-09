import json

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from odp.const import ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import PackageForm, ResourceSearchForm
from odp.ui.admin.views import utils
from odp.ui.base import api
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('packages', __name__)


@bp.route('/')
@api.view(ODPScope.PACKAGE_READ)
def index():
    page = request.args.get('page', 1)
    packages = api.get(f'/package/?page={page}')
    return render_template(
        'package_index.html',
        packages=packages,
        buttons=[
            create_btn(enabled=ODPScope.PACKAGE_WRITE in g.user_permissions),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.PACKAGE_READ)
def detail(id):
    package = api.get(f'/package/{id}')
    resources = api.get(f'/resource/', package_id=id, size=0)  # don't paginate

    return render_template(
        'package_detail.html',
        package=package,
        resources=resources,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.PACKAGE_WRITE in g.user_permissions),
            delete_btn(object_id=id, enabled=ODPScope.PACKAGE_WRITE in g.user_permissions, prompt_args=(id,)),
        ]
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.PACKAGE_WRITE)
def create():
    form = PackageForm(request.form)
    utils.populate_provider_choices(form.provider_id, include_none=True)
    utils.populate_metadata_schema_choices(form.schema_id)

    resource_search_form = ResourceSearchForm()
    utils.populate_provider_choices(resource_search_form.resource_provider_id, include_none=True)

    if request.method == 'POST' and form.validate():
        try:
            package = api.post('/package/', dict(
                provider_id=form.provider_id.data,
                schema_id=form.schema_id.data,
                metadata=json.loads(form.metadata.data),
                notes=form.notes.data,
                resource_ids=form.resource_ids.data,
            ))
            flash(f"Package {package['id']} has been created.", category='success')
            return redirect(url_for('.detail', id=package['id']))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'package_edit.html',
        form=form,
        resource_search_form=resource_search_form,
    )


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.PACKAGE_WRITE)
def edit(id):
    package = api.get(f'/package/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs empty multiselect field
    if request.method == 'POST':
        form = PackageForm(request.form)
    else:
        form = PackageForm(data=package)

    utils.populate_provider_choices(form.provider_id)
    utils.populate_metadata_schema_choices(form.schema_id)

    resources = api.get(f'/resource/', package_id=id, size=0)  # don't paginate
    # formatting of checkbox labels must match that of addResources() in the template
    form.resource_ids.choices = [
        (res['id'], f"{res['title']} [{res['filename']} | {res['size']} | {res['mimetype']}]")
        for res in resources['items']
    ]

    resource_search_form = ResourceSearchForm()
    utils.populate_provider_choices(resource_search_form.resource_provider_id)

    if request.method == 'POST' and form.validate():
        try:
            api.put(f'/package/{id}', dict(
                provider_id=form.provider_id.data,
                schema_id=form.schema_id.data,
                metadata=json.loads(form.metadata.data),
                notes=form.notes.data,
                resource_ids=form.resource_ids.data,
            ))
            flash(f'Package {id} has been updated.', category='success')
            return redirect(url_for('.detail', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'package_edit.html',
        package=package,
        form=form,
        resource_search_form=resource_search_form,
    )


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.PACKAGE_WRITE)
def delete(id):
    api.delete(f'/package/{id}')
    flash(f'Package {id} has been deleted.', category='success')
    return redirect(url_for('.index'))


@bp.route('/fetch-resources/<provider_id>')
# no @api.view because this is called via ajax
def fetch_resources(provider_id):
    """Endpoint for populating resource selection popup."""
    include_packaged = request.args.get('include_packaged')
    try:
        return api.get(
            '/resource/',
            provider_id=provider_id,
            exclude_packaged=not include_packaged,
            # XXX we can render in a scrollable modal, but
            #  this might be a problem for high volume providers:
            size=0,
        )
    except ODPAPIError as e:
        abort(e.status_code, e.error_detail)
