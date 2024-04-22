from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user

from app.admin import bp
from app.models import db, User, Song, PlayLogs


@bp.route('/admin-login', methods=['GET'])
def login():
    return render_template('admin/login.html')


@bp.route('/admin-login', methods=['POST'])
def do_login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.where(User.user_type == 'admn').where(User.email == email).where(
        User.password == password).first()
    if not user:
        flash("Credential not match for any admin", "message")
        return redirect(url_for('admin.login'))
    else:
        login_user(user)
        return redirect(url_for('main.index'))


@bp.route('/admin-console', methods=['GET'])
@login_required
def console():
    song_ids, song_counts = total_song_play_24h()
    creators = User.query.filter_by(user_type='crtr').all()
    songs = Song.query.all()
    users = User.query.all()
    return render_template('admin/console.html', creators=creators, songs=songs, song_ids=song_ids, users=users,
                           song_counts=list(song_counts.values()))


@bp.route('/add-creator-blacklist/<int:user_id>', methods=['GET'])
@login_required
def add_to_blacklist(user_id):
    user = User.query.get(user_id)
    user.is_allowed_to_create = 0
    db.session.commit()
    return redirect(url_for('admin.console'))


@bp.route('/add-creator-whitelist/<int:user_id>', methods=['GET'])
@login_required
def add_to_whitelist(user_id):
    user = User.query.get(user_id)
    user.is_allowed_to_create = 1
    db.session.commit()
    return redirect(url_for('admin.console'))


@bp.route('/flag-song/<int:song_id>', methods=['GET'])
@login_required
def flag_song(song_id):
    song = Song.query.get(song_id)
    song.is_active = False
    db.session.commit()
    return redirect(url_for('admin.console'))


@bp.route('/unflag-song/<int:song_id>', methods=['GET'])
@login_required
def unflag_song(song_id):
    song = Song.query.get(song_id)
    song.is_active = True
    db.session.commit()
    return redirect(url_for('admin.console'))


def total_song_play_24h():
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=96)
    play_logs = PlayLogs.query.filter(PlayLogs.datetime.between(start_time, end_time)).all()

    # Step 2: Process Data
    song_counts = {}
    for log in play_logs:
        song_id = log.song.title
        song_counts[song_id] = song_counts.get(song_id, 0) + 1

    # Prepare data for Chart.js
    song_ids = list(song_counts.keys())

    return song_ids, song_counts
