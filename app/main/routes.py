import os
import random
import urllib.parse
from datetime import datetime

from flask import render_template, request, flash, redirect, url_for, send_from_directory
from flask.json import dump
from flask_login import login_required, login_user, current_user, logout_user
from sqlalchemy import or_, func
from sqlalchemy.sql import text

from app.main import bp
from app.models import db, User, Language, Genre, Song, Rating, Album, PlayListParent, PlayListChildren, PlayLogs

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@bp.route('/')
@login_required
def index():
    songs = Song.query.order_by(text("id desc")).all()
    albums = Album.query.all()
    artists = User.query.filter_by(user_type='crtr').all()
    return render_template('user/home.html', songs=songs, albums=albums, artists=artists)


@bp.route('/register', methods=['GET'])
def register():
    return render_template('auth/register.html')


@bp.route('/register', methods=['POST'])
def register_user():
    email = request.form.get('email')
    if User.query.filter_by(email=email).all():
        flash("User already exists with same email address, Try using another email")
        return redirect(url_for('main.register'))
    else:
        name = request.form.get('fullname')
        password = request.form.get('password')
        user = User(name=name, email=email, password=password, is_active=True, is_allowed_to_create=True)
        db.session.add(user)
        db.session.commit()
        if login_user(user, remember=True):
            return redirect(url_for('main.index'))
        else:
            return redirect(url_for('main.register'))


@bp.route('/login', methods=['GET'])
def login():
    return render_template('auth/login.html')


@bp.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.where(or_(User.user_type == 'crtr', User.user_type == 'user')).where(User.email == email).where(
        User.password == password).first()
    if not user:
        flash("User not found", "message")
        return redirect(url_for('main.login'))
    else:
        login_user(user)
        return redirect(url_for('main.index'))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/profile', methods=['GET'])
@login_required
def profile():
    user = User.query.filter_by(id=current_user.id).first()
    return render_template('user/profile.html', user=user)


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    user = User.query.filter_by(id=current_user.id).first()

    if user.password == request.form.get('current_password'):
        if request.form.get('verify_password') == request.form.get('password'):
            user.password = request.form.get('password')
            db.session.commit()
            flash("Password changed successfully")
            return redirect('/profile')
        else:
            flash("New Password is not matching")
            return redirect('/profile')

    else:
        flash("Password is not valid")
        return redirect('/profile')


@bp.route('/upload-picture', methods=['POST'])
def change_profile_picture():
    user = User.query.get(current_user.id)
    file = request.files['profile_picture']
    if file.filename != '':
        filename = user.name + str(random.randint(100, 1000)) + file.filename
        file.save('app/storage/thumbnails/user/' + filename)
        user.profile_photo_file = filename
        db.session.commit()
    return redirect('/profile')


@bp.route('/search', methods=['GET'])
@login_required
def search():
    search_text = request.args.get('query')
    rating = request.args.get('rating')
    search_query = "%{}%".format(search_text)
    if rating is not None:
        song_result = db.session.query(Song).join(Rating,
                                                  Song.id == Rating.song_id).group_by(
            Song.id).filter(Song.title.like(search_query)).having(func.avg(Rating.rating) >= int(rating)).having(
            func.avg(Rating.rating) < int(rating) + 1).all()
    else:
        song_result = Song.query.filter(Song.title.like(search_query)).all()
    albums_result = Album.query.filter(Album.album_name.like(search_query)).all()
    artists_result = User.query.filter(User.name.like(search_query)).filter_by(user_type='crtr').all()

    return render_template('user/search-result.html',
                           song_result=song_result,
                           albums_result=albums_result,
                           artists_result=artists_result)


# SONG

@bp.route('/play-song/<int:song_id>', methods=['GET'])
@login_required
def play_song(song_id):
    rating = Rating.query.filter_by(song_id=song_id, user_id=current_user.id).first()
    song = Song.query.get(song_id)
    average_rating = song.get_average_rating()
    playlists = PlayListParent.query.filter_by(user_id=current_user.id)

    whatsapp_text_url_encoded = urllib.parse.quote(
        "Hey,  Just stumbled upon this cool track and couldn't resist sharing it with you \n*{song_name}*\nlink: {link} ".format(
            song_name=song.title, link=request.url))
    return render_template('user/play-song.html', song=song, rating=rating, average_rating=average_rating,
                           playlists=playlists, wa_text=whatsapp_text_url_encoded)


@bp.route('/log-play', methods=['POST'])
def log_song_play():
    song_id = request.form.get('song_id')
    log_song_with_user(song_id)
    return 'Logged'


@bp.route('/rate-song/<song_id>/<rating>', methods=['GET'])
@login_required
def rate_song(song_id, rating):
    rating_model = Rating.query.filter_by(song_id=song_id, user_id=current_user.id).first()
    if rating_model:
        rating_model.rating = rating
    else:
        db.session.add(Rating(song_id=song_id, user_id=current_user.id, rating=rating))

    db.session.commit()
    return 'Done'


# END SONG


# ALBUM
@bp.route('/index-album/<int:aid>', methods=['GET'])
@login_required
def view_album(aid):
    album = Album.query.get(aid)
    return render_template('user/album-index.html', album=album)


# END ALBUM

# PLAYLIST
@bp.route('/index-playlist', methods=['GET'])
@login_required
def all_playlists():
    playlists = PlayListParent.query.filter_by(user_id=current_user.id).all()

    selected_playlist_id = request.args.get('active')
    selected_playlist = PlayListChildren.query.filter_by(playlist_p_id=selected_playlist_id).all()
    return render_template('user/playlist-index.html', playlists=playlists, selected_playlist=selected_playlist)


@bp.route('/create-playlist', methods=['GET'])
@login_required
def create_playlist():
    return render_template('user/playlist-create.html')


@bp.route('/create-playlist', methods=['POST'])
@login_required
def store_playlist():
    playlist_name = request.form.get('playlist_name')
    pl = PlayListParent(playlist_name=playlist_name, is_public=False, user_id=current_user.id)
    db.session.add(pl)
    db.session.commit()
    return redirect(url_for('main.all_playlists'))


@bp.route('/add-to-playlist', methods=['POST'])
@login_required
def add_to_playlist():
    playlist_p_id = request.form.get('playlist_id')
    song_id = request.form.get('song_id')
    already_exist = PlayListChildren.query.filter_by(playlist_p_id=playlist_p_id, song_id=song_id).first()
    if not already_exist:
        pl = PlayListChildren(playlist_p_id=playlist_p_id, song_id=song_id)
        db.session.add(pl)
        db.session.commit()
    else:
        flash("Already added to the playlist")
    return redirect(url_for('main.play_song', song_id=song_id))


# END PLAYLIST


@bp.route('/storage/<folder>/<file>')
@bp.route('/storage/<folder>')
@login_required
def serve_file(folder, file=''):
    if file != '' and len(file):
        if folder == 'tsong':
            folder = 'thumbnails/song'
        elif folder == 'talbum':
            folder = 'thumbnails/album'
        elif folder == 'tuser':
            folder = 'thumbnails/user'
        else:
            folder = 'songs'
        return send_from_directory(base_dir + '/storage/' + folder, file)
    else:
        return ''


def log_song_with_user(song_id):
    last_play = PlayLogs.query.filter_by(song_id=song_id, user_id=current_user.id).order_by(text("id desc")).first()
    if last_play:
        total_minutes = (datetime.utcnow() - last_play.datetime).total_seconds()
        song = Song.query.get(song_id)

        if total_minutes > song.duration:
            log = PlayLogs(song_id=song_id, user_id=current_user.id, datetime=datetime.utcnow())
            db.session.add(log)

    else:
        log = PlayLogs(song_id=song_id, user_id=current_user.id, datetime=datetime.utcnow())
        db.session.add(log)
    db.session.commit()


@bp.route('/migrate')
def migrate():
    try:
        # User.__table__.create(db.engine)
        # db.drop_all(bind=None, tables=[Song.__table__])
        # db.create_all(bind=None, tables=[Song.__table__])
        db.drop_all()
        db.create_all()
        seed()
    except Exception as error:
        return str(error)

    return 'Done   '


@bp.route('/seed_data')
def seed():
    languages = [
        {"lang_name": "English"},
        {"lang_name": "Hindi"},
        {"lang_name": "Bengali"},
        {"lang_name": "Telugu"},
        {"lang_name": "Marathi"},
        {"lang_name": "Tamil"},
        {"lang_name": "Urdu"},
        {"lang_name": "Gujarati"},
        {"lang_name": "Kannada"},
        {"lang_name": "Oriya"},
        {"lang_name": "Punjabi"},
        {"lang_name": "Malayalam"},
        {"lang_name": "Assamese"},
        {"lang_name": "Sanskrit"},
        {"lang_name": "Konkani"},
        {"lang_name": "Manipuri"},
        {"lang_name": "Nepali"},
        {"lang_name": "Sindhi"},
        {"lang_name": "Kashmiri"},
        {"lang_name": "Dogri"},
        {"lang_name": "Bodo"},
    ]

    # Add data to the database
    for lang_data in languages:
        language = Language(**lang_data)
        db.session.add(language)

    indian_genres = [
        {"genre_name": "Genral"},
        {"genre_name": "Pop"},
        {"genre_name": "Rock"},
        {"genre_name": "Hip-Hop"},
        {"genre_name": "Jazz"},
        {"genre_name": "Classical"},
        {"genre_name": "Remix"},
        {"genre_name": "Electronic"},
        {"genre_name": "Country"},
        {"genre_name": "Blues"},
        {"genre_name": "Reggae"},
        {"genre_name": "R&B"},
        {"genre_name": "Bollywood"},
        {"genre_name": "Carnatic"},
        {"genre_name": "Hindustani Classical"},
        {"genre_name": "Bhangra"},
        {"genre_name": "Tollywood"},
        {"genre_name": "Punjabi Pop"},
        {"genre_name": "Rabindra Sangeet"},
        {"genre_name": "Ghazal"},
        {"genre_name": "Indi-Pop"},
        {"genre_name": "Folk Music"},
    ]

    # Add data to the database
    for genre_data in indian_genres:
        genre = Genre(**genre_data)
        db.session.add(genre)

    db.session.commit()

    return redirect('/')
