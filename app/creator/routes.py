import random
from datetime import datetime

from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import text

from app.creator import bp
from app.models import db, User, Language, Song, Album, Genre, PlayListChildren, Rating, PlayLogs


@bp.route('/creator_studio')
@login_required
def home():
    all_songs = Song.query.filter_by(artist_id=current_user.id).all()
    albums = Album.query.filter_by(creator_id=current_user.id).all()
    with db.engine.begin() as conn:
        rating = conn.execute(text(
            "SELECT avg(rating) from ratings where song_id in (select id from song where artist_id={user_id}) ".format(
                user_id=current_user.id))).fetchall()
        plays = conn.execute(text(
            "SELECT count(id) from play_logs where song_id in (select id from song where artist_id={user_id}) ".format(
                user_id=current_user.id))).fetchall()
        average_rating = (rating[0][0])
        total_plays = (plays[0][0])
    return render_template('creator/creator-profile.html', all_songs=all_songs, albums=albums,
                           average_rating=average_rating, total_plays=total_plays)


@bp.route('/public-profile/<int:creator_id>', methods=['GET'])
@login_required
def profile(creator_id):
    user = User.query.get(creator_id)
    # return current_user.user_type
    with db.engine.begin() as conn:
        rating = conn.execute(text(
            "SELECT avg(rating) from ratings where song_id in (select id from song where artist_id={user_id}) ".format(
                user_id=user.id))).fetchall()
        plays = conn.execute(text(
            "SELECT count(id) from play_logs where song_id in (select id from song where artist_id={user_id}) ".format(
                user_id=user.id))).fetchall()
    average_rating = (rating[0][0])
    total_plays = (plays[0][0])
    return render_template('creator/public-profile.html', creator=user, average_rating=average_rating,
                           total_plays=total_plays)


@bp.route('/creator/add_song', methods=['GET'])
@login_required
def add_song():
    languages = Language.query.all()

    albums = Album.query.filter_by(creator_id=current_user.id).all()
    # return current_user.user_type
    return render_template('creator/create-song.html', albums=albums, languages=languages)


@bp.route('/edit-song/<int:song_id>', methods=['GET'])
@login_required
def edit_song(song_id):
    languages = Language.query.all()
    genres = Genre.query.all()
    albums = Album.query.filter_by(creator_id=current_user.id).all()
    song = Song.query.filter_by(artist_id=current_user.id, id=song_id).first()
    return render_template('creator/edit-song.html', song=song, languages=languages, genres=genres, albums=albums)


@bp.route('/update-song/<int:song_id>', methods=['POST'])
@login_required
def update_song(song_id):
    song = Song.query.filter_by(id=song_id).first()

    song.title = request.form.get('song_name')
    song.album_id = request.form.get('album_id')
    song.language_id = request.form.get('language_id')
    song.lyrics = request.form.get('lyrics')
    if request.form.get('release_date') != '':
        song.release_year = request.form.get('release_date')

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = request.form.get('song_name') + str(random.randint(100, 1000)) + file.filename
        file.save('app/storage/songs/' + filename)
        song.duration = request.form.get('duration')
        song.file_path = filename

    if 'thumbnail' in request.files and request.files['thumbnail'].filename != '':
        thumbnail = request.files['thumbnail']
        thumbnail_name = request.form.get('song_name') + str(random.randint(100, 1000)) + thumbnail.filename
        thumbnail.save('app/storage/thumbnails/song/' + thumbnail_name)
        song.thumbnail = thumbnail_name

    db.session.commit()
    return redirect(url_for('main.play_song', song_id=song_id))


@bp.route('/delete-song/<int:song_id>', methods=['GET'])
@login_required
def delete_song(song_id):
    try:
        Song.query.filter_by(id=song_id).delete()
        PlayListChildren.query.filter_by(song_id=song_id).delete()
        Rating.query.filter_by(song_id=song_id).delete()
        PlayLogs.query.filter_by(song_id=song_id).delete()
    except Exception as error:
        return str(error)
    finally:
        db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/creator/store_song', methods=['POST'])
@login_required
def store_song():
    song_title = request.form.get('song_name')
    album_id = request.form.get('album_id')
    language_id = request.form.get('language_id')
    lyrics = request.form.get('lyrics')
    file = request.files['file']
    thumbnail = request.files['thumbnail']
    html_date = request.form.get('release_date')
    duration = request.form.get('duration')

    if file.filename != '':
        filename = song_title + str(random.randint(100, 1000)) + file.filename
        file.save('app/storage/songs/' + filename)
    else:
        filename = ''

    if thumbnail.filename != '':
        thumbnail_name = song_title + str(random.randint(100, 1000)) + thumbnail.filename
        thumbnail.save('app/storage/thumbnails/song/' + thumbnail_name)
    else:
        thumbnail_name = ''
    if html_date != '':
        date_obj = datetime.strptime(html_date, '%Y-%m-%d')
    else:
        date_obj = datetime.utcnow()
    new_song = Song(title=song_title,
                    album_id=album_id,
                    lyrics=lyrics,
                    language_id=language_id,
                    is_active=True,
                    release_year=date_obj,
                    artist_id=current_user.id,
                    duration=duration,
                    file_path=filename,
                    thumbnail=thumbnail_name)

    db.session.add(new_song)
    db.session.commit()

    return redirect(url_for('creator.home'))


@bp.route('/creator/add_album', methods=['GET'])
@login_required
def add_album():
    # return current_user.user_type
    genres = Genre.query.all()
    return render_template('creator/create-album.html', genres=genres)


@bp.route('/creator/edit_album/<int:album_id>', methods=['GET'])
@login_required
def edit_album(album_id):
    genres = Genre.query.all()
    album = Album.query.filter_by(album_id=album_id).first()

    return render_template('creator/edit-album.html', album=album, genres=genres)


@bp.route('/creator/delete_album/<int:album_id>', methods=['GET'])
@login_required
def delete_album(album_id):
    album = Album.query.filter_by(album_id=album_id).delete()
    Song.query.filter_by(album_id=album_id).delete()
    db.session.commit()
    return redirect(url_for('creator.home'))


@bp.route('/creator/update_album/<int:album_id>', methods=['POST'])
@login_required
def update_album(album_id):
    album = Album.query.get(album_id)
    album.album_name = request.form.get('album_name')
    album.genre_id = request.form.get('genre_id')
    file = request.files['file']

    if file.filename != '':
        filename = album.album_name + str(random.randint(100, 1000)) + file.filename
        file.save('app/storage/thumbnails/album/' + filename)
        album.thumbnail = filename
    db.session.commit()

    return redirect(url_for('creator.home'))


@bp.route('/creator/store_album', methods=['POST'])
@login_required
def store_album():
    album_name = request.form.get('album_name')
    genre_id = request.form.get('genre_id')
    file = request.files['file']

    if file.filename != '':
        filename = album_name + str(random.randint(100, 1000)) + file.filename
        file.save('app/storage/thumbnails/album/' + filename)
    else:
        filename = ''

    new_album = Album(album_name=album_name, thumbnail=filename, creator_id=current_user.id, genre_id=genre_id,
                      is_active=True)
    db.session.add(new_album)
    db.session.commit()

    return redirect(url_for('creator.home'))


@bp.route('/become_creator')
@login_required
def become_creator():
    user = User.query.filter_by(id=current_user.id).first()
    user.user_type = 'crtr'
    user.api_token = random.randint(10000000,90000000)
    db.session.commit()
    return redirect(url_for('creator.home'))
