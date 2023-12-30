from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('schemas', __name__)


@bp.route('/')
@api.view(ODPScope.SCHEMA_READ)
def index():
    page = request.args.get('page', 1)
    schemas = api.get(f'/schema/?schema_type=metadata&page={page}')
    return render_template('schema_index.html', schemas=schemas)


@bp.route('/<id>')
@api.view(ODPScope.SCHEMA_READ)
def detail(id):
    schema = api.get(f'/schema/{id}')
    return render_template('schema_detail.html', schema=schema)
