from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user

from odp.const import ODPScope
from odp.ui.admin.forms import CurationSubmissionForm, SubmissionFilterForm, SubmissionAcceptForm
from odp.ui.base import api
from odp.ui.base.templates import edit_btn
from odp.ui.base.views import utils
from odp.ui.admin.views.utils import populate_collection_choices

bp = Blueprint('submissions', __name__)


@bp.route('/')
@api.view(ODPScope.RECORD_READ)
def index():
    page = request.args.get('page', 1)

    filter_form = SubmissionFilterForm(request.form, data=request.args)

    filter_form.status.choices = [
        'all',
        'editing',
        'submitted'
    ]

    filter_status = request.args.get('status', 'all')

    submissions = api.get('/submission/', page=page, status=filter_status)

    return render_template(
        'submission_index.html',
        filter_form=filter_form,
        submissions=submissions,
    )


@bp.route('/<id>')
@api.view(ODPScope.RECORD_READ)
def detail(id):
    submission = api.get(f'/submission/admin/{id}')

    accept_form = SubmissionAcceptForm(request.form)

    populate_collection_choices(accept_form.collection)

    return render_template(
        'submission_detail.html',
        submission=submission,
        accept_form=accept_form,
        buttons=[
            edit_btn(object_id=id)
        ]
    )


@bp.route('/<id>/submit', methods=['GET', 'POST'])
@api.view(ODPScope.RECORD_READ)
def submit(id):
    print('Submit')
    return True


@bp.route('/<id>/delete', methods=['GET', 'POST'])
@api.view(ODPScope.RECORD_READ)
def delete(id):
    print('Delete')
    return True


@bp.route('/<id>/edit', methods=['GET', 'POST'])
@api.view(ODPScope.RECORD_READ)
def edit(id):
    submission = api.get(f'/submission/admin/{id}')

    submission_data = submission['data']

    form = CurationSubmissionForm(request.form, data=submission_data)

    utils.populate_keywords_choices(form.keywords)
    utils.populate_instruments_choices(form.instruments)

    form.keywords.data = submission_data.get('keywords')
    form.instruments.data = submission_data.get('instruments')

    if request.method == 'POST' and form.validate():
        cleaned_data = utils.clean_submission_data(form.data)

        api.put(f'/submission/{id}', dict(
            cleaned_data
        ))
        flash(f'Record {id} has been updated.', category='success')
        return redirect(url_for('.detail', id=id))

    return render_template(
        'submission_edit.html',
        submission=submission,
        form=form
    )


@bp.route('/orcid/<id>')
@api.view(ODPScope.RECORD_READ)
def get_orcid_info(id):
    if not current_user.is_authenticated:
        flash('Please log in to access that page.', 'warning')
        return redirect(url_for('.index'))

    return utils.get_orcid_info(id)
