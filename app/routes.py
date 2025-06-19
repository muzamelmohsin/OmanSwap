from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.models import db, User, Post, ExchangeRequest, Category
import os

main = Blueprint('main', __name__, template_folder='templates')

OMAN_PROVINCES = [
    "Muscat", "Dhofar", "Musandam", "Al Buraimi", "Ad Dakhiliyah",
    "North Al Batinah", "South Al Batinah", "South Al Sharqiyah",
    "North Al Sharqiyah", "Al Dhahirah", "Al Wusta"
]



@main.route('/')
def home():
    return render_template('home.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        bio = request.form.get('bio')
        phone_number = request.form['phone_number']
        province = request.form['province']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('main.register'))

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            bio=bio,
            phone_number=phone_number,
            province=province
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html', provinces=OMAN_PROVINCES)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    category = request.args.get('category')
    
    query = Post.query.filter(
        Post.user_id != current_user.id,
        Post.status != 'accepted'  # This hides accepted posts
    )

    if category:
        query = query.filter(Post.category == category)

    posts = query.all()
    categories = ['Books', 'Electronics', 'Musical Instruments']
    return render_template('dashboard.html', posts=posts, categories = [cat.name for cat in Category.query.order_by(Category.name).all()], selected_category=category)



@main.route('/my-posts')
@login_required
def my_posts():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template('my_posts.html', posts=posts)

@main.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        province = request.form['province']
        phone = request.form['phone']
        image_file = request.files.get('image')

        filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            image_file.save(upload_path)

        post = Post(
            title=title,
            description=description,
            category=category,
            province=province,
            phone=phone,
            image=filename,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully.')
        return redirect(url_for('main.my_posts'))
    return render_template('create_post.html', provinces=OMAN_PROVINCES, categories = [cat.name for cat in Category.query.order_by(Category.name).all()])

@main.route('/exchange/<int:post_id>', methods=['GET', 'POST'])
@login_required
def exchange(post_id):
    target_post = Post.query.get_or_404(post_id)
    my_posts = Post.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        my_item_id = request.form.get('my_item_id')
        message = request.form.get('message', '')
        if not my_item_id:
            flash("You must select one of your items to propose an exchange.")
            return redirect(url_for('main.exchange', post_id=post_id))

        new_exchange = ExchangeRequest(
            proposer_id=current_user.id,
            proposer_post_id=my_item_id,
            target_post_id=post_id,
            message=message
        )
        db.session.add(new_exchange)
        db.session.commit()
        flash("Exchange request sent.")
        return redirect(url_for('main.dashboard'))

    if not my_posts:
        flash("You must create a post first to send exchange requests.")
        return redirect(url_for('main.create_post'))

    return render_template('exchange.html', target_post=target_post, my_posts=my_posts)

@main.route('/notifications')
@login_required
def notifications():
    incoming = ExchangeRequest.query.join(Post, ExchangeRequest.target_post_id == Post.id)\
        .filter(
            Post.user_id == current_user.id,
            ExchangeRequest.is_accepted == False,
            ExchangeRequest.is_rejected == False
        ).all()

    outgoing = ExchangeRequest.query.filter_by(proposer_id=current_user.id).all()

    return render_template('notifications.html', incoming=incoming, outgoing=outgoing)



@main.route('/accept-exchange/<int:exchange_id>', methods=['POST'])
@login_required
def accept_exchange(exchange_id):
    exch = ExchangeRequest.query.get_or_404(exchange_id)
    target_post = exch.target_post

    if target_post.user_id != current_user.id:
        flash("Unauthorized: You can only accept requests for your own posts.")
        return redirect(url_for('main.notifications'))

    exch.is_accepted = True
    target_post.status = 'accepted'

    proposer_post = Post.query.get(exch.proposer_post_id)
    if proposer_post:
        proposer_post.status = 'accepted'

    db.session.commit()
    flash("Exchange accepted.")
    return redirect(url_for('main.notifications'))


@main.route('/reject-exchange/<int:exchange_id>', methods=['POST'])
@login_required
def reject_exchange(exchange_id):
    exch = ExchangeRequest.query.get_or_404(exchange_id)
    target_post = exch.target_post

    if target_post.user_id != current_user.id:
        flash("Unauthorized: You can only reject requests for your own posts.")
        return redirect(url_for('main.notifications'))

    exch.is_rejected = True
    db.session.commit()
    flash("Exchange rejected.")
    return redirect(url_for('main.notifications'))

@main.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        flash("You can only edit your own posts.")
        return redirect(url_for('main.my_posts'))

    if request.method == 'POST':
        post.title = request.form['title']
        post.description = request.form['description']
        post.category = request.form['category']
        post.province = request.form['province']
        post.phone = request.form['phone']

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            from werkzeug.utils import secure_filename
            import os
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            image_file.save(upload_path)
            post.image = filename

        db.session.commit()
        flash("Post updated.")
        return redirect(url_for('main.my_posts'))

    return render_template('edit_post.html', post=post, provinces=OMAN_PROVINCES, categories = [cat.name for cat in Category.query.order_by(Category.name).all()])


@main.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        flash("You can only delete your own posts.")
        return redirect(url_for('main.my_posts'))

    # Delete related exchange requests (both incoming and outgoing)
    ExchangeRequest.query.filter(
        (ExchangeRequest.target_post_id == post_id) |
        (ExchangeRequest.proposer_post_id == post_id)
    ).delete(synchronize_session=False)

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.")
    return redirect(url_for('main.my_posts'))


@main.route('/history')
@login_required
def history():
    accepted_posts = Post.query.filter_by(user_id=current_user.id, status='accepted').all()

    accepted_exchanges = ExchangeRequest.query.join(Post, ExchangeRequest.target_post_id == Post.id)\
        .filter(
            (ExchangeRequest.proposer_id == current_user.id) |
            (Post.user_id == current_user.id),
            ExchangeRequest.is_accepted == True
        ).all()

    return render_template('history.html', posts=accepted_posts, exchanges=accepted_exchanges)


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.username = request.form['username']
        user.phone_number = request.form['phone_number']
        user.bio = request.form['bio']
        user.province = request.form['province']
        

        db.session.commit()
        flash("Profile updated.")
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=user, provinces=OMAN_PROVINCES)


@main.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    users = User.query.all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin.html', users=users, categories=categories)


@main.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.username = request.form['username']
        user.phone_number = request.form['phone_number']
        user.bio = request.form['bio']
        user.province = request.form['province']
        user.role = request.form['role']

        new_password = request.form.get('new_password')
        if new_password:
            user.password = generate_password_hash(new_password)


        db.session.commit()
        flash("User updated.")
        return redirect(url_for('main.admin_panel'))

    return render_template('edit_user.html', user=user, provinces=OMAN_PROVINCES)



@main.route('/admin/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_post(post_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.description = request.form['description']
        post.category = request.form['category']
        post.province = request.form['province']
        post.phone = request.form['phone']

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            from werkzeug.utils import secure_filename
            import os
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            image_file.save(upload_path)
            post.image = filename

        db.session.commit()
        flash("Post updated by admin.")
        return redirect(url_for('main.admin_panel'))

    return render_template('admin_edit_post.html', post=post, provinces=OMAN_PROVINCES, categories = [cat.name for cat in Category.query.order_by(Category.name).all()])


@main.route('/admin/user-posts/<int:user_id>')
@login_required
def admin_user_posts(user_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id).all()
    return render_template('admin_user_posts.html', posts=posts, user=user)

@main.route('/admin/add-category', methods=['POST'])
@login_required
def add_category():
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    new_cat = request.form.get('new_category', '').strip()
    if new_cat and not Category.query.filter_by(name=new_cat).first():
        db.session.add(Category(name=new_cat))
        db.session.commit()
        flash("Category added.")
    else:
        flash("Invalid or duplicate category.")
    return redirect(url_for('main.admin_panel'))


@main.route('/admin/report')
@login_required
def exchange_report():
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    stats = {
        "users": User.query.count(),
        "posts": Post.query.count(),
        "total_requests": ExchangeRequest.query.count(),
        "accepted": ExchangeRequest.query.filter_by(is_accepted=True).count(),
        "rejected": ExchangeRequest.query.filter_by(is_rejected=True).count(),
        "pending": ExchangeRequest.query.filter_by(is_accepted=False, is_rejected=False).count()
    }
    return render_template('report.html', stats=stats)

@main.route('/admin/delete-category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    category = Category.query.get_or_404(category_id)
    posts_with_this_category = Post.query.filter_by(category=category.name).all()

    for post in posts_with_this_category:
        post.category = "Other"

    db.session.delete(category)
    db.session.commit()
    flash(f"Category '{category.name}' deleted. Associated posts moved to 'Other'.")
    return redirect(url_for('main.admin_panel'))


@main.route('/admin/delete-post/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    post = Post.query.get_or_404(post_id)

    # Delete all related exchange requests
    ExchangeRequest.query.filter(
        (ExchangeRequest.target_post_id == post.id) |
        (ExchangeRequest.proposer_post_id == post.id)
    ).delete(synchronize_session=False)

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.")
    return redirect(url_for('main.admin_user_posts', user_id=post.user_id))



@main.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)

    
    for post in user.posts:
        ExchangeRequest.query.filter(
            (ExchangeRequest.proposer_post_id == post.id) |
            (ExchangeRequest.target_post_id == post.id)
        ).delete(synchronize_session=False)

    
    for post in user.posts:
        db.session.delete(post)

    
    ExchangeRequest.query.filter_by(proposer_id=user.id).delete(synchronize_session=False)

    
    db.session.delete(user)
    db.session.commit()
    flash("User and all related data deleted.")
    return redirect(url_for('main.admin_panel'))


@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pwd = request.form['current_password']
        new_pwd = request.form['new_password']
        confirm_pwd = request.form['confirm_password']

        if not check_password_hash(current_user.password, current_pwd):
            flash("Current password is incorrect.")
            return redirect(url_for('main.change_password'))

        if new_pwd != confirm_pwd:
            flash("New passwords do not match.")
            return redirect(url_for('main.change_password'))

        current_user.password = generate_password_hash(new_pwd)
        db.session.commit()
        flash("Password updated.")
        return redirect(url_for('main.profile'))

    return render_template('change_password.html')


