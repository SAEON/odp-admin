from flask import Blueprint, render_template, request

from odp.const import ODPScope
from odp.ui.base import api
from odp.ui.base.templates import create_btn, delete_btn, edit_btn

bp = Blueprint('keywords', __name__)


@bp.route('/')
@api.view(ODPScope.KEYWORD_READ_ALL)
def index():
    vocabulary_ids = request.args.getlist('vocabulary')
    page = request.args.get('page', 1)

    api_filter = ''
    ui_filter = ''
    for vocabulary_id in vocabulary_ids:
        api_filter += f'&vocabulary_id={vocabulary_id}'
        ui_filter += f'&vocabulary={vocabulary_id}'

    keywords = api.get(f'/keyword/?page={page}{api_filter}')

    return render_template(
        'keyword_index.html',
        keywords=keywords,
        filter_=ui_filter,
        buttons=[
            create_btn(scope=ODPScope.KEYWORD_ADMIN),
        ]
    )


@bp.route('/<id>')
@api.view(ODPScope.KEYWORD_READ_ALL)
def detail(id):
    keyword = api.get(f'/keyword/{id}')
    return render_template(
        'keyword_detail.html',
        keyword=keyword,
        buttons=[
            edit_btn(object_id=id, scope=ODPScope.KEYWORD_ADMIN),
            delete_btn(object_id=id, scope=ODPScope.KEYWORD_ADMIN, prompt_args=(id,)),
        ]
    )
