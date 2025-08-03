from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from . import db
from .models import Post
from flask import current_app

import os
from werkzeug.utils import secure_filename
from .models import Post, Comment, User

UPLOAD_FOLDER = 'app/static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return redirect(url_for('main.feed'))

@main.route('/feed')
@login_required
def feed():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('feed.html', user=current_user, posts=posts)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/create', methods=['POST'])
@login_required
def create():
    content = request.form.get('content')
    if content:
        post = Post(content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
    return redirect(url_for('main.feed'))

@main.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    from .models import User
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', profile_user=user)

@main.route('/edit-bio', methods=['POST'])
@login_required
def edit_bio():
    new_bio = request.form.get('bio')
    current_user.bio = new_bio
    db.session.commit()
    return redirect(url_for('main.profile', user_id=current_user.id))

@main.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('main.feed'))

@main.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        post.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('main.feed'))

    return render_template('edit_post.html', post=post)

@main.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('comment')
    post = Post.query.get_or_404(post_id)
    if content:
        comment = Comment(content=content, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for('main.feed'))

@main.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
    else:
        post.liked_by.append(current_user)
    db.session.commit()
    return redirect(url_for('main.feed'))
@main.route('/upload_pic', methods=['POST'])
@login_required
def upload_pic():
    file = request.files.get('profile_pic')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        upload_path = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_path, exist_ok=True)  # make folder if not exists

        filepath = os.path.join(upload_path, filename)
        file.save(filepath)

        current_user.profile_pic = filename
        db.session.commit()
        flash("Profile picture updated!", "success")
    else:
        flash("Invalid file type.", "danger")

    return redirect(url_for('main.profile', user_id=current_user.id))
