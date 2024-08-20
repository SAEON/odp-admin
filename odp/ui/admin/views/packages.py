from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from odp.const import ODPPackageTag, ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import PackageForm
from odp.ui.base import api
from odp.ui.base.forms import ResourceSearchForm
from odp.ui.base.lib import tags, utils
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('packages', __name__)


@bp.route('/')
@api.view(ODPScope.PACKAGE_READ_ALL)
def index():
    page = request.args.get('page', 1)
    provider_id = request.args.get('provider')
    ui_filter = f'&provider={provider_id}' if provider_id else ''

    packages = api.get(
        '/package/all/',
        provider_id=provider_id,
        page=page,
    )

    return render_template(
        'package_index.html',
        packages=packages,
        filter_=ui_filter,
        buttons=[
            create_btn(scope=ODPScope.PACKAGE_ADMIN),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.PACKAGE_READ_ALL)
def detail(id):
    package = api.get(f'/package/all/{id}')
    resources = utils.pagify(package['resources'])

    doi_tag = tags.get_tag_instance(package, ODPPackageTag.DOI)
    contrib_tags = tags.get_tag_instances(package, ODPPackageTag.CONTRIBUTOR)

    return render_template(
        'package_detail.html',
        package=package,
        resources=resources,
        doi_tag=doi_tag,
        contrib_tags=contrib_tags,
        buttons=[
            edit_btn(object_id=id, scope=ODPScope.PACKAGE_ADMIN),
            delete_btn(object_id=id, scope=ODPScope.PACKAGE_ADMIN, prompt_args=(id,)),
        ]
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.PACKAGE_ADMIN)
def create():
    form = PackageForm(request.form)
    utils.populate_provider_choices(form.provider_id, include_none=True)

    resource_search_form = ResourceSearchForm()
    utils.populate_provider_choices(resource_search_form.resource_provider_id, include_none=True)

    if request.method == 'POST' and form.validate():
        try:
            package = api.post('/package/admin/', dict(
                provider_id=form.provider_id.data,
                title=form.title.data,
                resource_ids=form.resource_ids.data,
            ))
            flash(f"Package <b>{package['title']}</b> has been created.", category='success')
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
@api.view(ODPScope.PACKAGE_ADMIN)
def edit(id):
    package = api.get(f'/package/all/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs empty multiselect field
    if request.method == 'POST':
        form = PackageForm(request.form)
    else:
        form = PackageForm(data=package)

    utils.populate_provider_choices(form.provider_id)

    # formatting of checkbox labels must match that of addResources() in the template
    form.resource_ids.choices = [
        (res['id'], f"{res['title']} [{res['filename']} | {res['size']} | {res['mimetype']}]")
        for res in package['resources']
    ]

    resource_search_form = ResourceSearchForm()
    utils.populate_provider_choices(resource_search_form.resource_provider_id)

    if request.method == 'POST' and form.validate():
        try:
            api.put(f'/package/admin/{id}', dict(
                provider_id=form.provider_id.data,
                title=(title := form.title.data),
                resource_ids=form.resource_ids.data,
            ))
            flash(f'Package <b>{title}</b> has been updated.', category='success')
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
@api.view(ODPScope.PACKAGE_ADMIN)
def delete(id):
    api.delete(f'/package/admin/{id}')
    flash(f'Package {id} has been deleted.', category='success')
    return redirect(url_for('.index'))


@bp.route('/fetch-resources/<provider_id>')
# no @api.view because this is called via ajax
def fetch_resources(provider_id):
    """Endpoint for populating resource selection popup."""
    include_packaged = request.args.get('include_packaged')
    try:
        return api.get(
            '/resource/all/',
            provider_id=provider_id,
            exclude_packaged=not include_packaged,
            size=0,
        )
    except ODPAPIError as e:
        abort(e.status_code, e.error_detail)
