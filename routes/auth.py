from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from database.models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not full_name or not email or not password or not confirm_password:
            flash('All fields are required!', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered!', 'danger')
            return render_template('register.html')
            
        # Create new user
        new_user = User(
            full_name=full_name,
            email=email,
            is_admin=False
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not email or not password:
            flash('Please enter email and password.', 'danger')
            return render_template('login.html')
            
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html')
            
        login_user(user, remember=remember)
        
        # Redirect if it's admin or regular user
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
            
        if user.is_admin:
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin.dashboard'))
            
        flash(f'Welcome back, {user.full_name}!', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.landing'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            
            if not full_name or not email:
                flash('Name and Email cannot be empty.', 'danger')
                return render_template('profile.html')
                
            # Email uniqueness check (excluding self)
            existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing_user:
                flash('Email is already in use by another account.', 'danger')
                return render_template('profile.html')
                
            current_user.full_name = full_name
            current_user.email = email
            db.session.commit()
            flash('Profile details updated successfully!', 'success')
            
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_new_password = request.form.get('confirm_new_password')
            
            if not current_password or not new_password or not confirm_new_password:
                flash('All password fields are required.', 'danger')
                return render_template('profile.html')
                
            if not current_user.check_password(current_password):
                flash('Incorrect current password.', 'danger')
                return render_template('profile.html')
                
            if new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return render_template('profile.html')
                
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully!', 'success')
            
        return redirect(url_for('auth.profile'))
        
    return render_template('profile.html')
