from pathlib import Path

from flask import Flask

from odp.config import config
from odp.const import ODPArchive, ODPScope
from odp.const.hydra import HydraScope
from odp.ui import base
from odp.ui.admin import views


def create_app():
    """
    Flask application factory.
    """
    app = Flask(__name__)
    app.config.update(
        UI_CLIENT_ID=config.ODP.ADMIN.UI_CLIENT_ID,
        UI_CLIENT_SECRET=config.ODP.ADMIN.UI_CLIENT_SECRET,
        UI_CLIENT_SCOPE=[HydraScope.OPENID, HydraScope.OFFLINE_ACCESS] + [s.value for s in ODPScope],
        SECRET_KEY=config.ODP.ADMIN.FLASK_SECRET,
        UPLOAD_ARCHIVE_ID=ODPArchive.ODP_UPLOAD,
    )

    base.init_app(app, user_api=True, template_dir=Path(__file__).parent / 'templates')
    views.init_app(app)

    return app
