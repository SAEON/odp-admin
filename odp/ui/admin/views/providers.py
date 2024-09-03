from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from odp.const import ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import ProviderForm, UserFilterForm
from odp.ui.base import api
from odp.ui.base.lib import utils
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('providers', __name__)


@bp.route('/')
@api.view(ODPScope.PROVIDER_READ_ALL)
def index():
    page = request.args.get('page', 1)
    providers = api.get('/provider/all/', page=page, sort='key')
    return render_template(
        'provider_index.html',
        providers=providers,
        buttons=[
            create_btn(scope=ODPScope.PROVIDER_ADMIN),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.PROVIDER_READ_ALL)
def detail(id):
    provider = api.get(f'/provider/all/{id}')
    audit_records = api.get(f'/provider/{id}/audit')
    return render_template(
        'provider_detail.html',
        provider=provider,
        audit_records=audit_records,
        buttons=[
            edit_btn(object_id=id, scope=ODPScope.PROVIDER_ADMIN),
            delete_btn(object_id=id, scope=ODPScope.PROVIDER_ADMIN, prompt_args=(id,)),
        ]
    )


@bp.route('/<id>/audit/<audit_id>')
@api.view(ODPScope.PROVIDER_READ)
def audit_detail(id, audit_id):
    provider_audit = api.get(f'/provider/{id}/audit/{audit_id}')
    return render_template('provider_audit_detail.html', audit=provider_audit)


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.PROVIDER_ADMIN)
def create():
    form = ProviderForm(request.form)
    user_filter_form = UserFilterForm()
    utils.populate_role_choices(user_filter_form.role, include_none=True)

    if request.method == 'POST' and form.validate():
        try:
            provider = api.post('/provider/', dict(
                key=(key := form.key.data),
                name=form.name.data,
                user_ids=form.user_ids.data,
            ))
            flash(f'Provider {key} has been created.', category='success')
            return redirect(url_for('.detail', id=provider['id']))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'provider_edit.html',
        form=form,
        user_filter_form=user_filter_form,
    )


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.PROVIDER_ADMIN)
def edit(id):
    provider = api.get(f'/provider/all/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs empty multiselect field
    if request.method == 'POST':
        form = ProviderForm(request.form)
    else:
        form = ProviderForm(data=provider)

    user_filter_form = UserFilterForm()
    utils.populate_role_choices(user_filter_form.role, include_none=True)

    users = api.get(f'/user/', provider_id=id, size=0)  # don't paginate
    # formatting of checkbox labels must match that of addUsers() in the template
    form.user_ids.choices = [
        (user['id'], f"{user['name']} | {user['email']}")
        for user in users['items']
    ]

    if request.method == 'POST' and form.validate():
        try:
            api.put(f'/provider/{id}', dict(
                key=(key := form.key.data),
                name=form.name.data,
                user_ids=form.user_ids.data,
            ))
            flash(f'Provider {key} has been updated.', category='success')
            return redirect(url_for('.detail', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(
        'provider_edit.html',
        provider=provider,
        form=form,
        user_filter_form=user_filter_form,
    )


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.PROVIDER_ADMIN)
def delete(id):
    api.delete(f'/provider/{id}')
    flash(f'Provider {id} has been deleted.', category='success')
    return redirect(url_for('.index'))


@bp.route('/fetch-users')
# no @api.view because this is called via ajax
def fetch_users():
    """Endpoint for populating user selection popup."""
    try:
        return api.get(
            '/user/',
            text_query=request.args.get('q'),
            role_id=request.args.get('role'),
            size=0,
        )
    except ODPAPIError as e:
        abort(e.status_code, e.error_detail)
