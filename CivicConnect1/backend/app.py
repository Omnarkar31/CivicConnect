import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'civicconnect_secure_789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/civic_connect_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
class Ward(db.Model):
    __tablename__ = 'wards'
    id = db.Column(db.Integer, primary_key=True)
    ward_number = db.Column(db.String(10), unique=True, nullable=False)
    ward_code = db.Column(db.String(20), unique=True, nullable=False)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='citizen') 
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    ward = db.relationship('Ward', backref='users')

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Submitted')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='complaints')

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    title = db.Column(db.String(200))
    contractor_name = db.Column(db.String(100))
    budget = db.Column(db.Numeric(15, 2))
    deadline = db.Column(db.Date)
    status = db.Column(db.String(50), default='Started')
    progress_percentage = db.Column(db.Integer, default=0)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    priority = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ward_admin':
            flash("Unauthorized access. Admin only.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.role == 'ward_admin' else 'citizen_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    ward = Ward.query.filter_by(ward_number=request.form.get('ward_number'), ward_code=request.form.get('ward_code')).first()
    if not ward:
        flash('Invalid Ward details.', 'danger')
        return redirect(url_for('login'))

    new_user = User(
        name=request.form.get('name'),
        email=request.form.get('email'),
        password_hash=generate_password_hash(request.form.get('password')),
        role='citizen',
        ward_id=ward.id
    )
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

# --- DASHBOARD LOGIC (Synced with Template) ---

@app.route('/citizen/dashboard')
@login_required
def citizen_dashboard():
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(ward_id=current_user.ward_id).all()
    announcements = Announcement.query.filter_by(ward_id=current_user.ward_id).order_by(Announcement.created_at.desc()).all()
    return render_template('dashboard.html', complaints=complaints, projects=projects, announcements=announcements)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    complaints = Complaint.query.filter_by(ward_id=current_user.ward_id).all()
    projects = Project.query.filter_by(ward_id=current_user.ward_id).all()
    announcements = Announcement.query.filter_by(ward_id=current_user.ward_id).order_by(Announcement.created_at.desc()).all()
    return render_template('dashboard.html', complaints=complaints, projects=projects, announcements=announcements)

# --- ACTION ENDPOINTS (Fixing BuildErrors) ---

@app.route('/submit-complaint', methods=['POST'])
@login_required
def submit_complaint():
    new_c = Complaint(
        user_id=current_user.id,
        ward_id=current_user.ward_id,
        category=request.form.get('category'),
        description=request.form.get('description')
    )
    db.session.add(new_c)
    db.session.commit()
    flash('Complaint submitted!', 'success')
    return redirect(url_for('citizen_dashboard'))

@app.route('/post-announcement', methods=['POST'])
@login_required
@admin_required
def post_announcement():
    new_a = Announcement(
        ward_id=current_user.ward_id,
        title=request.form.get('title'),
        message=request.form.get('message'),
        priority=request.form.get('priority')
    )
    db.session.add(new_a)
    db.session.commit()
    flash('Announcement posted!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/add-project', methods=['POST'])
@login_required
@admin_required
def add_project():
    deadline_date = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date()
    new_p = Project(
        ward_id=current_user.ward_id,
        title=request.form.get('title'),
        contractor_name=request.form.get('contractor'),
        budget=request.form.get('budget'),
        deadline=deadline_date,
        progress_percentage=request.form.get('progress')
    )
    db.session.add(new_p)
    db.session.commit()
    flash('Project added!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/gov/create-admin', methods=['GET', 'POST'])
def gov_create_admin():
    if request.method == 'POST':
        unique_code = f"WARD-{secrets.token_hex(3).upper()}"
        new_ward = Ward(ward_number=request.form['ward_number'], ward_code=unique_code)
        db.session.add(new_ward); db.session.flush()
        new_admin = User(name=request.form['name'], email=request.form['email'], password_hash=generate_password_hash(request.form['password']), role='ward_admin', ward_id=new_ward.id)
        db.session.add(new_admin); db.session.commit()
        return render_template('gov_success.html', code=unique_code, ward=request.form['ward_number'], email=request.form['email'])
    return render_template('gov_create.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)