from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('resources', __name__)


@bp.route('/')
@api.view(ODPScope.RESOURCE_READ_ALL)
def index():
    page = request.args.get('page', 1)
    archive_id = request.args.get('archive')
    package_id = request.args.get('package')
    provider_id = request.args.get('provider')

    ui_filter = ''
    if archive_id:
        ui_filter += f'&archive={archive_id}'
    if package_id:
        ui_filter += f'&package={package_id}'
    if provider_id:
        ui_filter += f'&provider={provider_id}'

    resources = api.get(
        '/resource/all/',
        page=page,
        archive_id=archive_id,
        package_id=package_id,
        provider_id=provider_id,
    )

    return render_template(
        'resource_index.html',
        resources=resources,
        filter_=ui_filter,
    )


@bp.route('/<id>')
@api.view(ODPScope.RESOURCE_READ_ALL)
def detail(id):
    resource = api.get(f'/resource/all/{id}')

    return render_template(
        'resource_detail.html',
        resource=resource,
    )
