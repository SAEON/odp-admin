from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('resources', __name__)


@bp.route('/')
@api.view(ODPScope.RESOURCE_READ)
def index():
    page = request.args.get('page', 1)
    resources = api.get(f'/resource/?page={page}')
    return render_template('resource_index.html', resources=resources)


@bp.route('/<id>')
@api.view(ODPScope.RESOURCE_READ)
def detail(id):
    resource = api.get(f'/resource/{id}')
    return render_template('resource_detail.html', resource=resource)
