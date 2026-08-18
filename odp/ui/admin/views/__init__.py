from flask import Flask


def init_app(app: Flask):
    from . import catalogs, collections, downloads, home, providers, records, schemas, tags, vocabularies

    app.register_blueprint(home.bp)
    app.register_blueprint(catalogs.bp, url_prefix='/catalogs')
    app.register_blueprint(collections.bp, url_prefix='/collections')
    app.register_blueprint(downloads.bp, url_prefix='/downloads')
    app.register_blueprint(providers.bp, url_prefix='/providers')
    app.register_blueprint(records.bp, url_prefix='/records')
    app.register_blueprint(schemas.bp, url_prefix='/schemas')
    app.register_blueprint(tags.bp, url_prefix='/tags')
    app.register_blueprint(vocabularies.bp, url_prefix='/vocabularies')
