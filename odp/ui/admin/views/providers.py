from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.client import ODPAPIError
from odp.const import ODPScope
from odp.ui.admin.forms import ProviderForm
from odp.ui.base import api
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('providers', __name__)


@bp.route('/')
@api.view(ODPScope.PROVIDER_READ)
def index():
    page = request.args.get('page', 1)
    providers = api.get(f'/provider/?page={page}')
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
    return render_template(
        'provider_view.html',
        provider=provider,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.PROVIDER_ADMIN in g.user_permissions),
            delete_btn(object_id=id, enabled=ODPScope.PROVIDER_ADMIN in g.user_permissions, prompt_args=(id,)),
        ]
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.PROVIDER_ADMIN)
def create():
    form = ProviderForm(request.form)

    if request.method == 'POST' and form.validate():
        try:
            api.post('/provider/', dict(
                id=(id := form.id.data),
                name=form.name.data,
            ))
            flash(f'Provider {id} has been created.', category='success')
            return redirect(url_for('.view', id=id))

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
            api.put('/provider/', dict(
                id=id,
                name=form.name.data,
            ))
            flash(f'Provider {id} has been updated.', category='success')
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
