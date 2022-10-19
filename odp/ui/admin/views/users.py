from flask import Blueprint, flash, redirect, render_template, request, url_for

from odp.const import ODPScope
from odp.ui import api
from odp.ui.admin.forms import UserForm
from odp.ui.admin.views import utils

bp = Blueprint('users', __name__)


@bp.route('/')
@api.client(ODPScope.USER_READ)
def index():
    page = request.args.get('page', 1)
    users = api.get(f'/user/?page={page}')
    return render_template('user_list.html', users=users)


@bp.route('/<id>')
@api.client(ODPScope.USER_READ)
def view(id):
    user = api.get(f'/user/{id}')
    return render_template('user_view.html', user=user)


@bp.route('/<id>/edit', methods=('GET', 'POST'))
@api.client(ODPScope.USER_ADMIN)
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

        except api.ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template('user_edit.html', user=user, form=form)


@bp.route('/<id>/delete', methods=('POST',))
@api.client(ODPScope.USER_ADMIN)
def delete(id):
    api.delete(f'/user/{id}')
    flash(f'User {id} has been deleted.', category='success')
    return redirect(url_for('.index'))
