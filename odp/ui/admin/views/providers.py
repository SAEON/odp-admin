from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.const import ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import ProviderForm
from odp.ui.base import api
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('providers', __name__)


@bp.route('/')
@api.view(ODPScope.PROVIDER_READ)
def index():
    page = request.args.get('page', 1)
    providers = api.get('/provider/', page=page, sort='key')
    return render_template(
        'provider_list.html',
        providers=providers,
        buttons=[
            create_btn(enabled=ODPScope.PROVIDER_ADMIN in g.user_permissions),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.PROVIDER_READ)
def view(id):
    provider = api.get(f'/provider/{id}')
    audit_records = api.get(f'/provider/{id}/audit')
    return render_template(
        'provider_view.html',
        provider=provider,
        audit_records=audit_records,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.PROVIDER_ADMIN in g.user_permissions),
            delete_btn(object_id=id, enabled=ODPScope.PROVIDER_ADMIN in g.user_permissions, prompt_args=(id,)),
        ]
    )


@bp.route('/<id>/audit/<audit_id>')
@api.view(ODPScope.PROVIDER_READ)
def view_audit_detail(id, audit_id):
    audit_detail = api.get(f'/provider/{id}/audit/{audit_id}')
    return render_template('provider_audit_view.html', audit=audit_detail)


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.PROVIDER_ADMIN)
def create():
    form = ProviderForm(request.form)

    if request.method == 'POST' and form.validate():
        try:
            provider = api.post('/provider/', dict(
                key=(key := form.key.data),
                name=form.name.data,
            ))
            flash(f'Provider {key} has been created.', category='success')
            return redirect(url_for('.view', id=provider['id']))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('provider_edit.html', form=form)


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.PROVIDER_ADMIN)
def edit(id):
    provider = api.get(f'/provider/{id}')
    form = ProviderForm(request.form, data=provider)

    if request.method == 'POST' and form.validate():
        try:
            api.put(f'/provider/{id}', dict(
                key=(key := form.key.data),
                name=form.name.data,
            ))
            flash(f'Provider {key} has been updated.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('provider_edit.html', provider=provider, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.PROVIDER_ADMIN)
def delete(id):
    api.delete(f'/provider/{id}')
    flash(f'Provider {id} has been deleted.', category='success')
    return redirect(url_for('.index'))
