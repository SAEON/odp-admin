from importlib import import_module

from flask import Flask


def init_app(app: Flask):
    from . import home

    app.register_blueprint(home.bp)

    for view in (
            'archives',
            'catalogs',
            'clients',
            'collections',
            'packages',
            'providers',
            'records',
            'resources',
            'roles',
            'schemas',
            'tags',
            'users',
            'vocabularies'
    ):
        mod = import_module(f'odp.ui.admin.views.{view}')
        app.register_blueprint(mod.bp, url_prefix=f'/{view}')
