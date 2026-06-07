from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.models import db, User, Prediction, Watchlist, ContactMessage

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    """
    Ensure the logged-in user is an administrator.
    """
    if not current_user.is_admin:
        flash("Unauthorized access. Administrative privileges required.", "danger")
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    # Gather statistics
    user_count = User.query.count()
    prediction_count = Prediction.query.count()
    message_count = ContactMessage.query.count()
    watchlist_count = Watchlist.query.count()
    
    # Get all users (sorted by join date)
    users = User.query.order_by(User.join_date.desc()).all()
    
    # Get all contact messages
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    
    # Get latest 10 predictions across the system
    predictions = Prediction.query.order_by(Prediction.prediction_date.desc()).limit(15).all()
    
    return render_template('admin.html',
                           user_count=user_count,
                           prediction_count=prediction_count,
                           message_count=message_count,
                           watchlist_count=watchlist_count,
                           users=users,
                           messages=messages,
                           predictions=predictions)

@admin_bp.route('/message/read/<int:msg_id>', methods=['POST'])
def mark_message_read(msg_id):
    msg = ContactMessage.query.get_or_400(msg_id)
    msg.is_read = True
    db.session.commit()
    flash('Message marked as read.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/message/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    msg = ContactMessage.query.get_or_400(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/user/toggle-admin/<int:user_id>', methods=['POST'])
def toggle_user_admin(user_id):
    # Prevent self-demotion
    if user_id == current_user.id:
        flash('You cannot change your own administrative status!', 'warning')
        return redirect(url_for('admin.dashboard'))
        
    user = User.query.get_or_400(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    status = "promoted to Admin" if user.is_admin else "demoted to User"
    flash(f"User {user.full_name} has been {status}.", 'success')
    return redirect(url_for('admin.dashboard'))
