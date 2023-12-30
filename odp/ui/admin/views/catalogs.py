from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('catalogs', __name__)


@bp.route('/')
@api.view(ODPScope.CATALOG_READ)
def index():
    page = request.args.get('page', 1)
    catalogs = api.get(f'/catalog/?page={page}')
    return render_template('catalog_index.html', catalogs=catalogs)


@bp.route('/<id>')
@api.view(ODPScope.CATALOG_READ)
def detail(id):
    catalog = api.get(f'/catalog/{id}')
    return render_template('catalog_detail.html', catalog=catalog)
