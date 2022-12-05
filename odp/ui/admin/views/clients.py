from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from wtforms.validators import input_required

from odp.client import ODPAPIError
from odp.const import ODPScope
from odp.ui.admin.forms import ClientForm
from odp.ui.admin.views import utils
from odp.ui.base import api
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('clients', __name__)


@bp.route('/')
@api.view(ODPScope.CLIENT_READ)
def index():
    page = request.args.get('page', 1)
    clients = api.get(f'/client/?page={page}')
    return render_template(
        'client_list.html',
        clients=clients,
        buttons=[
            create_btn(enabled=ODPScope.CLIENT_ADMIN in g.user_permissions),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.CLIENT_READ)
def view(id):
    client = api.get(f'/client/{id}')
    return render_template(
        'client_view.html',
        client=client,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.CLIENT_ADMIN in g.user_permissions),
            delete_btn(object_id=id, enabled=ODPScope.CLIENT_ADMIN in g.user_permissions, prompt_args=(id,)),
        ]
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.CLIENT_ADMIN)
def create():
    form = ClientForm(request.form)
    form.secret.validators = [input_required()]
    utils.populate_collection_choices(form.collection_ids)
    utils.populate_scope_choices(form.scope_ids)

    if request.method == 'POST' and form.validate():
        try:
            api.post('/client/', dict(
                id=(id := form.id.data),
                name=form.name.data,
                secret=form.secret.data,
                collection_specific=form.collection_specific.data,
                collection_ids=form.collection_ids.data,
                scope_ids=form.scope_ids.data,
                grant_types=form.grant_types.data,
                response_types=form.response_types.data,
                redirect_uris=form.redirect_uris.data.split(),
                post_logout_redirect_uris=form.post_logout_redirect_uris.data.split(),
                token_endpoint_auth_method=form.token_endpoint_auth_method.data,
                allowed_cors_origins=form.allowed_cors_origins.data.split(),
            ))
            flash(f'Client {id} has been created.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('client_edit.html', form=form)


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.CLIENT_ADMIN)
def edit(id):
    client = api.get(f'/client/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs empty multiselect field
    if request.method == 'POST':
        form = ClientForm(request.form)
    else:
        form = ClientForm(data=client | {'collection_ids': list(client['collection_keys'].values())})

    form.secret.description = 'Client secret will remain unchanged if left blank.'
    utils.populate_collection_choices(form.collection_ids)
    utils.populate_scope_choices(form.scope_ids)

    if request.method == 'POST' and form.validate():
        try:
            api.put('/client/', dict(
                id=id,
                name=form.name.data,
                secret=form.secret.data or None,
                collection_specific=form.collection_specific.data,
                collection_ids=form.collection_ids.data,
                scope_ids=form.scope_ids.data,
                grant_types=form.grant_types.data,
                response_types=form.response_types.data,
                redirect_uris=form.redirect_uris.data.split(),
                post_logout_redirect_uris=form.post_logout_redirect_uris.data.split(),
                token_endpoint_auth_method=form.token_endpoint_auth_method.data,
                allowed_cors_origins=form.allowed_cors_origins.data.split(),
            ))
            flash(f'Client {id} has been updated.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('client_edit.html', client=client, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.CLIENT_ADMIN)
def delete(id):
    api.delete(f'/client/{id}')
    flash(f'Client {id} has been deleted.', category='success')
    return redirect(url_for('.index'))
