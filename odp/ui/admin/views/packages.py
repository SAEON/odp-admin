from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('packages', __name__)


@bp.route('/')
@api.view(ODPScope.PACKAGE_READ)
def index():
    page = request.args.get('page', 1)
    packages = api.get(f'/package/?page={page}')
    return render_template('package_index.html', packages=packages)


@bp.route('/<id>')
@api.view(ODPScope.PACKAGE_READ)
def detail(id):
    package = api.get(f'/package/{id}')
    return render_template('package_detail.html', package=package)
