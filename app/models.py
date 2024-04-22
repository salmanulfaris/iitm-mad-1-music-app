from app.extensions import db


class Album(db.Model):
    __tablename__ = "album"
    album_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    album_name = db.Column(db.String, nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.genre_id'), nullable=True)
    thumbnail = db.Column(db.String, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    creator = db.relationship('User', backref='albums')
    genre = db.relationship('Genre', backref='albums')


class Genre(db.Model):
    __tablename__ = "genre"
    genre_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    genre_name = db.Column(db.String, nullable=False)


class Language(db.Model):
    __tablename__ = "languages"
    lang_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    lang_name = db.Column(db.String, nullable=False)


class PlayLogs(db.Model):
    __tablename__ = "play_logs"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.DateTime)


class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    rating = db.Column(db.Float(2, 1), nullable=False)


class Song(db.Model):
    __tablename__ = "song"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.album_id'), nullable=True)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.lang_id'), nullable=True)
    thumbnail = db.Column(db.String, nullable=True)
    release_year = db.Column(db.Date, nullable=True)
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    file_path = db.Column(db.String, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    lyrics = db.Column(db.Text, nullable=True)
    album = db.relationship('Album', backref='songs')
    artist = db.relationship('User', backref='songs')
    language = db.relationship('Language', backref='songs')
    ratings = db.relationship('Rating', backref='song', lazy=True)
    play_logs = db.relationship('PlayLogs', backref='song', lazy=True)

    def get_total_plays(self):
        return PlayLogs.query.filter_by(song_id=self.id).count()

    def get_average_rating(self):
        ratings = [rating.rating for rating in self.ratings]
        if ratings:
            return round(sum(ratings) / len(ratings), 2)
        return 0


class PlayListParent(db.Model):
    __tablename__ = "playlist_parent"
    playlist_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    playlist_name = db.Column(db.Integer, nullable=False)
    is_public = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class PlayListChildren(db.Model):
    __tablename__ = "playlist_children"
    playlist_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    playlist_p_id = db.Column(db.Integer, db.ForeignKey('playlist_parent.playlist_id'))
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    parent = db.relationship('PlayListParent', backref='songs')
    song = db.relationship('Song')


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_photo_file = db.Column(db.String(100), nullable=True)
    user_type = db.Column(db.String(4), nullable=False, default='user')
    is_active = db.Column(db.Boolean(), nullable=False)
    api_token = db.Column(db.String(), nullable=True)
    is_allowed_to_create = db.Column(db.Boolean(), default=True)
    playlists = db.relationship('PlayListParent', backref='user')

    def get_id(self):
        return self.id

    def get(self):
        return self.query.filter_by(id=id).first()

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated and self.is_active

    # def is_authenticated(self):
    #     """Return True if the user is authenticated."""
    #     return self.is_active

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', " \
               f"user_type='{self.user_type}', is_active={self.is_active}, " \
               f"is_allowed_to_create={self.is_allowed_to_create})>"
