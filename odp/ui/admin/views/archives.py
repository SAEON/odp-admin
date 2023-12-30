from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('archives', __name__)


@bp.route('/')
@api.view(ODPScope.ARCHIVE_READ)
def index():
    page = request.args.get('page', 1)
    archives = api.get(f'/archive/?page={page}')
    return render_template('archive_index.html', archives=archives)


@bp.route('/<id>')
@api.view(ODPScope.ARCHIVE_READ)
def detail(id):
    archive = api.get(f'/archive/{id}')
    return render_template('archive_detail.html', archive=archive)
