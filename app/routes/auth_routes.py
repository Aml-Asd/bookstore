from flask import Blueprint, render_template, redirect, url_for, flash, request
from urllib.parse import urlsplit  # Changed from url_parse
from bookstore_flask_project.app import db
from bookstore_flask_project.app.models import User
from bookstore_flask_project.app.forms import LoginForm, RegistrationForm
from flask_login import login_user, logout_user, current_user, login_required

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role after login if already authenticated
        if current_user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('customer.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        # Security check for next_page
        if not next_page or urlsplit(next_page).netloc != '':
            if user.role == 'manager':
                next_page = url_for('manager.dashboard')
            else:
                next_page = url_for('customer.index')  # Default customer page
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('customer.index'))  # Redirect to homepage after logout


@bp.route('/signup', methods=['GET', 'POST'])  # Changed from /register to /signup
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('customer.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        # Default role is 'customer', set in model
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, your account has been created!', 'success')
        # Log in the new user automatically
        login_user(user)
        return redirect(url_for('customer.index'))  # Redirect to customer dashboard or homepage
    return render_template('auth/signup.html', title='Create Account', form=form)