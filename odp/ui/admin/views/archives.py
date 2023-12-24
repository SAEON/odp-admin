from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('archives', __name__)


@bp.route('/')
@api.view(ODPScope.ARCHIVE_READ)
def index():
    page = request.args.get('page', 1)
    archives = api.get(f'/archive/?page={page}')
    return render_template('archive_list.html', archives=archives)


@bp.route('/<id>')
@api.view(ODPScope.ARCHIVE_READ)
def view(id):
    archive = api.get(f'/archive/{id}')
    return render_template('archive_view.html', archive=archive)
