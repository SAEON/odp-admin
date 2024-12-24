from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('vocabularies', __name__)


@bp.route('/')
@api.view(ODPScope.VOCABULARY_READ)
def index():
    page = request.args.get('page', 1)
    vocabularies = api.get(f'/vocabulary/?page={page}')
    return render_template(
        'vocabulary_index.html',
        vocabularies=vocabularies,
    )


@bp.route('/<id>')
@api.view(ODPScope.VOCABULARY_READ)
def detail(id):
    vocabulary = api.get(f'/vocabulary/{id}')
    return render_template(
        'vocabulary_detail.html',
        vocabulary=vocabulary,
    )
