from flask import Blueprint, flash, redirect, render_template, request, url_for

from odp.const import ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import UserFilterForm, UserForm
from odp.ui.base import api
from odp.ui.base.lib import utils
from odp.ui.base.templates import delete_btn, edit_btn

bp = Blueprint('users', __name__)


@bp.route('/')
@api.view(ODPScope.USER_READ)
def index():
    page = request.args.get('page', 1)
    text_q = request.args.get('q')
    provider_id = request.args.get('provider')
    role_id = request.args.get('role')

    api_filter = ''
    ui_filter = ''
    if text_q:
        api_filter += f'&text_query={text_q}'
        ui_filter += f'&q={text_q}'
    if provider_id:
        api_filter += f'&provider_id={provider_id}'
        ui_filter += f'&provider={provider_id}'
    if role_id:
        api_filter += f'&role_id={role_id}'
        ui_filter += f'&role={role_id}'

    filter_form = UserFilterForm(request.args)
    utils.populate_provider_choices(filter_form.provider, include_none=True)
    utils.populate_role_choices(filter_form.role, include_none=True)

    users = api.get(f'/user/?page={page}{api_filter}')

    return render_template(
        'user_index.html',
        users=users,
        filter_=ui_filter,
        filter_form=filter_form,
    )


@bp.route('/<id>')
@api.view(ODPScope.USER_READ)
def detail(id):
    user = api.get(f'/user/{id}')
    return render_template(
        'user_detail.html',
        user=user,
        buttons=[
            edit_btn(object_id=id, scope=ODPScope.USER_ADMIN),
            delete_btn(object_id=id, scope=ODPScope.USER_ADMIN, prompt_args=(user['name'],)),
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
            return redirect(url_for('.detail', id=id))

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
