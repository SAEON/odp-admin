from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.client import ODPAPIError
from odp.const import ODPScope
from odp.ui.admin.forms import RoleForm
from odp.ui.admin.views import utils
from odp.ui.base import api
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('roles', __name__)


@bp.route('/')
@api.view(ODPScope.ROLE_READ)
def index():
    page = request.args.get('page', 1)
    roles = api.get(f'/role/?page={page}')
    return render_template(
        'role_list.html',
        roles=roles,
        buttons=[
            create_btn(enabled=ODPScope.ROLE_ADMIN in g.user_permissions),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.ROLE_READ)
def view(id):
    role = api.get(f'/role/{id}')
    return render_template(
        'role_view.html',
        role=role,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.ROLE_ADMIN in g.user_permissions),
            delete_btn(object_id=id, enabled=ODPScope.ROLE_ADMIN in g.user_permissions, prompt_args=(id,)),
        ]
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.ROLE_ADMIN)
def create():
    form = RoleForm(request.form)
    utils.populate_collection_choices(form.collection_ids)
    utils.populate_scope_choices(form.scope_ids, ('odp', 'client'))

    if request.method == 'POST' and form.validate():
        try:
            api.post('/role/', dict(
                id=(id := form.id.data),
                collection_specific=form.collection_specific.data,
                collection_ids=form.collection_ids.data,
                scope_ids=form.scope_ids.data,
            ))
            flash(f'Role {id} has been created.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('role_edit.html', form=form)


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.ROLE_ADMIN)
def edit(id):
    role = api.get(f'/role/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs empty multiselect field
    if request.method == 'POST':
        form = RoleForm(request.form)
    else:
        form = RoleForm(data=role | {'collection_ids': list(role['collection_keys'].values())})

    utils.populate_collection_choices(form.collection_ids)
    utils.populate_scope_choices(form.scope_ids, ('odp', 'client'))

    if request.method == 'POST' and form.validate():
        try:
            api.put('/role/', dict(
                id=id,
                collection_specific=form.collection_specific.data,
                collection_ids=form.collection_ids.data,
                scope_ids=form.scope_ids.data,
            ))
            flash(f'Role {id} has been updated.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('role_edit.html', role=role, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.ROLE_ADMIN)
def delete(id):
    api.delete(f'/role/{id}')
    flash(f'Role {id} has been deleted.', category='success')
    return redirect(url_for('.index'))
