from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from odp.client import ODPAPIError
from odp.const import ODPScope
from odp.ui.admin.forms import UserForm
from odp.ui.admin.views import utils
from odp.ui.base import api
from odp.ui.base.templates import delete_btn, edit_btn

bp = Blueprint('users', __name__)


@bp.route('/')
@api.view(ODPScope.USER_READ)
def index():
    page = request.args.get('page', 1)
    users = api.get(f'/user/?page={page}')
    return render_template('user_list.html', users=users)


@bp.route('/<id>')
@api.view(ODPScope.USER_READ)
def view(id):
    user = api.get(f'/user/{id}')
    return render_template(
        'user_view.html',
        user=user,
        buttons=[
            edit_btn(object_id=id, enabled=ODPScope.USER_ADMIN in g.user_permissions),
            delete_btn(object_id=id, enabled=ODPScope.USER_ADMIN in g.user_permissions, prompt_args=(user['name'],)),
        ]
    )


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.view(ODPScope.USER_ADMIN)
def edit(id):
    user = api.get(f'/user/{id}')

    # separate get/post form instantiation to resolve
    # ambiguity of missing vs empty multiselect field
    if request.method == 'POST':
        form = UserForm(request.form)
    else:
        form = UserForm(data=user)

    utils.populate_role_choices(form.role_ids)

    if request.method == 'POST' and form.validate():
        try:
            api.put('/user/', dict(
                id=id,
                active=form.active.data,
                role_ids=form.role_ids.data,
            ))
            flash(f'User {id} has been updated.', category='success')
            return redirect(url_for('.view', id=id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('user_edit.html', user=user, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.view(ODPScope.USER_ADMIN)
def delete(id):
    api.delete(f'/user/{id}')
    flash(f'User {id} has been deleted.', category='success')
    return redirect(url_for('.index'))
