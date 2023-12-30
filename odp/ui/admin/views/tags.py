from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('tags', __name__)


@bp.route('/')
@api.view(ODPScope.TAG_READ)
def index():
    page = request.args.get('page', 1)
    tags = api.get(f'/tag/?page={page}')
    return render_template('tag_index.html', tags=tags)


@bp.route('/<id>')
@api.view(ODPScope.TAG_READ)
def detail(id):
    tag = api.get(f'/tag/{id}')
    return render_template('tag_detail.html', tag=tag)
