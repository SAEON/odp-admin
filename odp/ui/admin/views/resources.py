import hashlib
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from odp.const import ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.admin.forms import ResourceUploadForm
from odp.ui.base import api
from odp.ui.base.lib import utils
from odp.ui.base.templates import create_btn

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
        buttons=[
            create_btn(scope=ODPScope.RESOURCE_ADMIN),
        ],
    )


@bp.route('/<id>')
@api.view(ODPScope.RESOURCE_READ_ALL)
def detail(id):
    resource = api.get(f'/resource/all/{id}')

    return render_template(
        'resource_detail.html',
        resource=resource,
    )


@bp.route('/new', methods=('GET', 'POST'))
@api.view(ODPScope.RESOURCE_ADMIN)
def create():
    upload_archive_id = current_app.config['UPLOAD_ARCHIVE_ID']
    upload_archive = api.get(f'/archive/{upload_archive_id}')
    upload_dir = Path(urlparse(upload_archive['url']).path)

    form = ResourceUploadForm(request.form)
    utils.populate_provider_choices(form.provider_id, include_none=True)

    if request.method == 'POST' and form.validate():
        provider = api.get(f'/provider/{form.provider_id.data}')
        folder = Path(provider['key']) / str(date.today())
        file = request.files.get('file')
        filename = secure_filename(file.filename)
        md5 = hashlib.md5(file.read()).hexdigest()
        size = file.tell()

        try:
            (upload_dir / folder).mkdir(mode=0o755, parents=True, exist_ok=True)

            filestem = (archive_filename := Path(filename)).stem
            n = 0
            while (savepath := upload_dir / folder / archive_filename).exists():
                n += 1
                archive_filename = archive_filename.with_stem(f'{filestem}_{n:03d}')

            file.seek(0)
            file.save(savepath)

            try:
                resource = api.post('/resource/admin/', dict(
                    title=(title := form.title.data),
                    description=form.description.data,
                    filename=filename,
                    mimetype=file.mimetype,
                    size=size,
                    md5=md5,
                    provider_id=form.provider_id.data,
                    archive_id=upload_archive_id,
                    archive_path=f'{folder / archive_filename}',
                ))

                flash(f'Resource {title} has been created.', category='success')
                return redirect(url_for('.detail', id=resource['id']))

            except ODPAPIError as e:
                if response := api.handle_error(e):
                    return response

        except OSError as e:
            flash(f'File upload failed: {e!r}', category='error')

    return render_template(
        'resource_upload.html',
        form=form,
    )
