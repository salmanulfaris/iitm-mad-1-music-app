from datetime import datetime

from flask import request
from flask_restful import Resource, marshal_with, fields, reqparse

from app.api.validation import BusinessValidationError, NotFoundError
from app.extensions import db
from app.models import Song, Album, User, Language

song_resource_field = {
    'id': fields.String,
    'title': fields.String,
    'album': fields.Nested({'album_name': fields.String, 'album_id': fields.Integer}),
    'artist': fields.Nested({'name': fields.String, 'artist_id': fields.Integer(attribute='id')}),
    'lyrics': fields.String,
    'duration': fields.Integer
}

album_resource_field = {
    'album_id': fields.String,
    'album_name': fields.String,
    'genre': fields.Nested({'genre_name': fields.String, 'genre_id': fields.Integer}),
    'songs': fields.Nested(
        {
            'id': fields.Integer,
            'title': fields.String,
            'lyrics': fields.String,
            'artist': fields.Nested(
                {
                    'id': fields.Integer,
                    'name': fields.String,
                }
            )
        }, True),
}


def validate_user(func):
    def wrapper(*args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('user_token', type=str, help='User ID is required', location='args')

        args = parser.parse_args()

        # Check if the user_id is provided
        if args['user_token'] is None:
            return {'error': 'User Token is required'}, 400

        user_token = args['user_token']
        if not User.query.filter_by(api_token=user_token).first():
            return {'error': 'Invalid User Token'}, 400

        return func(*args, **kwargs)

    return wrapper


class SongResource(Resource):
    @validate_user
    @marshal_with(song_resource_field)
    def get(self, id):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        return Song.query.filter_by(id=id, artist_id=user.id).first()

    @validate_user
    @marshal_with(song_resource_field)
    def put(self, id):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        song = Song.query.filter_by(artist_id=user.id, id=id).first()
        if request.form.get('song_name') is not None:
            song.title = request.form.get('song_name')
        if request.form.get('album_id') is not None:
            song.album_id = request.form.get('album_id')
        if request.form.get('language_id') is not None:
            song.language_id = request.form.get('language_id')
        if request.form.get('lyrics') is not None:
            song.lyrics = request.form.get('lyrics')
        db.session.commit()
        return song

    def delete(self, id):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        Song.query.filter_by(id=id, artist_id=user.id).delete()
        db.session.commit()
        return "Deleted song Successfully", 200


class SongListResource(Resource):
    @validate_user
    @marshal_with(song_resource_field)
    def get(self):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        return Song.query.filter_by(artist_id=user.id).all()

    @validate_user
    @marshal_with(song_resource_field)
    def post(self):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()

        song_title = request.form.get('song_name')
        album_id = request.form.get('album_id')
        language_id = request.form.get('language_id')
        lyrics = request.form.get('lyrics')
        html_date = request.form.get('release_date')
        duration = request.form.get('duration')

        if song_title is None:
            raise BusinessValidationError(status_code=422, error_code="SONG001",
                                          error_message="Title is required")

        if album_id is None or not Album.query.filter_by(creator_id=user.id, album_id=album_id).all():
            raise BusinessValidationError(status_code=422, error_code="SONG002",
                                          error_message="Valid Album is required")

        if language_id is None or not Language.query.filter_by(lang_id=language_id).all():
            raise BusinessValidationError(status_code=422, error_code="SONG003",
                                          error_message="Valid Language is required")

        if lyrics is None:
            raise BusinessValidationError(status_code=422, error_code="SONG004",
                                          error_message="Lyrics is required")

        if duration is None:
            raise BusinessValidationError(status_code=422, error_code="SONG005",
                                          error_message="Duration is required")

        if html_date != '' and html_date is not None:
            date_obj = datetime.strptime(html_date, '%Y-%m-%d')
        else:
            date_obj = datetime.utcnow()

        new_song = Song(title=song_title,
                        album_id=album_id,
                        lyrics=lyrics,
                        language_id=language_id,
                        is_active=True,
                        release_year=date_obj,
                        artist_id=user.id,
                        duration=duration,
                        file_path='',
                        thumbnail='')

        db.session.add(new_song)
        db.session.commit()

        return new_song, 201


class AlbumListResource(Resource):

    @marshal_with(album_resource_field)
    def get(self):

        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        return Album.query.filter_by(creator_id=user.id).all()

    @marshal_with(album_resource_field)
    def post(self):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        album_name = request.form.get('album_name')
        genre_id = request.form.get('genre_id')

        if album_name is None:
            raise BusinessValidationError(status_code=422, error_code="ALBM001",
                                          error_message="Album name is required")

        if genre_id is None:
            raise BusinessValidationError(status_code=422, error_code="ALBM002",
                                          error_message="Genre is required")

        new_album = Album(album_name=album_name, thumbnail='', creator_id=user.id, genre_id=genre_id,
                          is_active=True)
        db.session.add(new_album)
        db.session.commit()
        return new_album


class AlbumResource(Resource):

    @marshal_with(album_resource_field)
    def get(self, id):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        return Album.query.get(id)

    @marshal_with(album_resource_field)
    def put(self, id):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        album = Album.query.filter_by(creator_id=user.id, album_id=id).first()

        album_name = request.form.get('album_name')
        genre_id = request.form.get('genre_id')

        if album_name is not None:
            album.album_name = album_name

        if genre_id is not None:
            album.genre_id = genre_id

        db.session.commit()
        return album

    def delete(self, id):
        user = User.query.filter_by(api_token=request.args.get('user_token')).first()
        Album.query.filter_by(creator_id=user.id, album_id=id).delete()
        Song.query.filter_by(album_id=id).delete()
        db.session.commit()
        return {"data": "Deleted Successfully"}, 200
