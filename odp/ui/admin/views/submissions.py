from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user

from odp.const import ODPScope
from odp.const.db import SubmissionStatus
from odp.ui.admin.forms import CurationSubmissionForm, SubmissionFilterForm, SubmissionAcceptForm
from odp.ui.admin.views.utils import populate_collection_choices
from odp.ui.base import api
from odp.ui.base.views import utils

bp = Blueprint('submissions', __name__)


@bp.route('/')
@api.view(ODPScope.SUBMISSION_ADMIN)
def index():
    page = request.args.get('page', 1)

    filter_form = SubmissionFilterForm(request.form, data=request.args)

    filter_form.status.choices = [('all', 'All')] + [
        (status.value, status.name.replace('_', ' ').title())
        for status in SubmissionStatus
    ]

    filter_status = request.args.get('status', 'all')

    submissions = api.get('/submission/', page=page, status=filter_status)

    return render_template(
        'submission_index.html',
        filter_form=filter_form,
        submissions=submissions,
    )


@bp.route('/<id>')
@api.view(ODPScope.SUBMISSION_ADMIN)
def detail(id):
    submission = api.get(f'/submission/admin/{id}')

    submission_user = api.get(f'/user/{submission["user_id"]}')

    accept_form = SubmissionAcceptForm(request.form, data=submission)

    populate_collection_choices(accept_form.collection_id)

    buttons_enabled = (submission['status'] == SubmissionStatus.submitted)

    return render_template(
        'submission_detail.html',
        submission=submission,
        submission_user=submission_user,
        accept_form=accept_form,
        buttons_enabled=buttons_enabled,
    )


@bp.route('/<id>/accept', methods=['POST'])
@api.view(ODPScope.SUBMISSION_ADMIN)
def accept(id):
    accept_form = SubmissionAcceptForm(request.form)

    api.put(
        f'/submission/admin/{id}/accept',
        data=dict(),
        collection_id=accept_form.data['collection_id'],
        schema_id=accept_form.data['schema_id'],
        doi=accept_form.data['doi']
    )

    return redirect(url_for('.detail', id=id))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
@api.view(ODPScope.SUBMISSION_ADMIN)
def edit(id):
    submission = api.get(f'/submission/admin/{id}')

    submission_data = submission['data']

    form = CurationSubmissionForm(request.form, data=submission_data)

    utils.populate_keywords_choices(form.keywords)
    utils.populate_instruments_choices(form.instruments)
    utils.populate_location_choices(form.place_keywords)

    if request.method == 'GET':
        form.keywords.data = submission_data.get('keywords')
        form.instruments.data = submission_data.get('instruments')
        form.eov_keywords.data = submission_data.get('eov_keywords')
        form.ecv_keywords.data = submission_data.get('ecv_keywords')
        form.ebv_keywords.data = submission_data.get('ebv_keywords')
        form.eav_keywords.data = submission_data.get('eav_keywords')
        form.place_keywords.data = submission_data.get('place_keywords')

    if request.method == 'POST' and form.validate():
        cleaned_data = utils.clean_submission_data(form.data)

        api.put(
            f'/submission/admin/{id}',
            dict(
                data=cleaned_data
            )
        )
        flash(f'Record {id} has been updated.', category='success')
        return redirect(url_for('.detail', id=id))

    return render_template(
        'submission_edit.html',
        submission=submission,
        form=form
    )


@bp.route('/<id>/delete', methods=['GET', 'POST'])
@api.view(ODPScope.SUBMISSION_ADMIN)
def delete(id):
    api.delete(f'/submission/admin/{id}')

    flash(f'Record {id} has been delete.', category='success')

    return redirect(url_for('.index'))


@bp.route('/orcid/<id>')
@api.view(ODPScope.RECORD_READ)
def get_orcid_info(id):
    if not current_user.is_authenticated:
        flash('Please log in to access that page.', 'warning')
        return redirect(url_for('.index'))

    return utils.get_orcid_info(id)
