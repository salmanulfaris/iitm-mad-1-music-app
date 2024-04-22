from flask import Flask
from flask_restful import Api

from app.api import SongListResource, SongResource, AlbumResource, AlbumListResource
from app.extensions import db, login_manager
from app.models import User
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # api
    api = Api(app)

    #  extensions here
    login_manager.init_app(app)
    db.init_app(app)

    # Register blueprints here
    from app.main import bp as main_bp
    from app.creator import bp as creator_bp
    from app.admin import bp as admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(creator_bp)
    app.register_blueprint(admin_bp)

    # register Api Resource here
    api.add_resource(SongListResource, '/api/song')
    api.add_resource(SongResource, '/api/song/<int:id>')
    api.add_resource(AlbumListResource, '/api/album')
    api.add_resource(AlbumResource, '/api/album/<int:id>')

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
