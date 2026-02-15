import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'civic_connect_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/civic_connect_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'mov', 'avi', 'pdf'}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class Ward(db.Model):
    __tablename__ = 'wards'
    id = db.Column(db.Integer, primary_key=True)
    ward_number = db.Column(db.String(10), unique=True, nullable=False)
    ward_code = db.Column(db.String(50), nullable=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='citizen')
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    ward = db.relationship('Ward', backref='users')

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    file_path = db.Column(db.Text)  # comma-separated paths for citizen attachments
    work_photos = db.Column(db.Text)  # comma-separated paths for admin work-in-progress photos
    status = db.Column(db.String(30), default='Reviewing')  # Reviewing, In Process, Completed
    viewed_by_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='user_complaints')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.role in ('ward_admin', 'admin') else 'citizen_dashboard'))
        flash('Invalid Login', 'danger')
    return render_template('login.html')

@app.route('/gov/create', methods=['GET', 'POST'])
def gov_create_redirect():
    """Redirect old URL to secure URL so links keep working."""
    return redirect(url_for('gov_create'), code=302)

@app.route('/gov/secure/appoint-admin', methods=['GET', 'POST'])
def gov_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        ward_number = request.form.get('ward_number', '').strip()
        if not name or not email or not password or not ward_number:
            flash('Please fill all required fields.', 'danger')
            return render_template('gov_create.html')
        try:
            ward = Ward.query.filter_by(ward_number=ward_number).first()
            if not ward:
                code = f"WARD-{ward_number}-{uuid.uuid4().hex[:8].upper()}"
                ward = Ward(ward_number=ward_number, ward_code=code)
                db.session.add(ward)
                db.session.flush()
            else:
                code = getattr(ward, 'ward_code', None) or ''
                if not code:
                    code = f"WARD-{ward_number}-{uuid.uuid4().hex[:8].upper()}"
                    ward.ward_code = code
            if User.query.filter_by(email=email).first():
                flash('This email is already registered.', 'danger')
                return render_template('gov_create.html')
            admin = User(
                name=name, email=email,
                password_hash=generate_password_hash(password),
                role='ward_admin', ward_id=ward.id
            )
            db.session.add(admin)
            db.session.commit()
            session['gov_success'] = {'email': email, 'ward': ward_number, 'code': code}
            return redirect(url_for('gov_success'))
        except Exception as e:
            db.session.rollback()
            flash(f'Could not create admin. Check that the database has wards.ward_code and users tables. Error: {str(e)}', 'danger')
            return render_template('gov_create.html')
    return render_template('gov_create.html')

@app.route('/gov/secure/success')
def gov_success():
    data = session.pop('gov_success', None)
    if not data:
        return redirect(url_for('login'))
    return render_template('gov_success.html', email=data['email'], ward=data['ward'], code=data['code'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        ward_number = request.form.get('ward_number', '').strip()
        ward_code = request.form.get('ward_code', '').strip()
        address = request.form.get('address', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        if not name or not email or not password or not ward_number or not ward_code:
            flash('Please fill all required fields.', 'danger')
            return render_template('login.html')
        ward = Ward.query.filter_by(ward_number=ward_number).first()
        if not ward:
            flash('Invalid ward number.', 'danger')
            return render_template('login.html')
        if ward.ward_code and ward.ward_code != ward_code:
            flash('Invalid ward code.', 'danger')
            return render_template('login.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('login.html')
        user = User(
            name=name, email=email,
            password_hash=generate_password_hash(password),
            role='citizen', ward_id=ward.id,
            address=address, phone=phone
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/citizen/dashboard')
@login_required
def citizen_dashboard():
    view = request.args.get('view', 'default')
    # Force fresh read from DB so admin-updated status (Reviewing / In Process / Completed) is shown
    db.session.expire_all()
    complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    resp = make_response(render_template('citizen_dashboard.html', complaints=complaints, view=view))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not is_ward_admin():
        return redirect(url_for('citizen_dashboard'))
    view = request.args.get('view', 'default')
    complaints = Complaint.query.filter_by(ward_id=current_user.ward_id).order_by(Complaint.created_at.desc()).all()
    unviewed_count = len(complaints)
    try:
        if hasattr(Complaint, 'viewed_by_admin'):
            unviewed_count = Complaint.query.filter_by(ward_id=current_user.ward_id, viewed_by_admin=False).count()
            if view == 'complaints' and complaints:
                for c in complaints:
                    if not c.viewed_by_admin:
                        c.viewed_by_admin = True
                        db.session.add(c)
                db.session.commit()
                unviewed_count = Complaint.query.filter_by(ward_id=current_user.ward_id, viewed_by_admin=False).count()
    except Exception:
        pass
    return render_template('admin_dashboard.html', complaints=complaints, view=view, unviewed_count=unviewed_count)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit-complaint', methods=['POST'])
@login_required
def submit_complaint():
    paths = []
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'complaints')
    os.makedirs(upload_dir, exist_ok=True)
    if 'attachments' in request.files:
        for f in request.files.getlist('attachments'):
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                name = f"{uuid.uuid4().hex}.{ext}"
                path = os.path.join(upload_dir, name)
                f.save(path)
                paths.append('complaints/' + name)
    new_c = Complaint(
        user_id=current_user.id,
        ward_id=current_user.ward_id,
        category=request.form.get('category'),
        description=request.form.get('description'),
        file_path=','.join(paths) if paths else None
    )
    db.session.add(new_c)
    db.session.commit()
    return redirect(url_for('citizen_dashboard', view='track'))

def is_ward_admin():
    return getattr(current_user, 'role', None) in ('ward_admin', 'admin')

@app.route('/admin/complaint/<int:cid>/update', methods=['POST'])
@login_required
def update_complaint(cid):
    if not is_ward_admin():
        flash('Not allowed.', 'danger')
        return redirect(url_for('citizen_dashboard'))
    c = Complaint.query.get_or_404(cid)
    if c.ward_id != current_user.ward_id:
        flash('Not allowed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    new_status = request.form.get('status')
    if new_status in ('Reviewing', 'In Process', 'Completed'):
        c.status = new_status
        db.session.add(c)
        db.session.flush()
    paths = []
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'work_photos')
    os.makedirs(upload_dir, exist_ok=True)
    if 'work_photos' in request.files:
        for f in request.files.getlist('work_photos'):
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                if ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                    continue
                name = f"{uuid.uuid4().hex}.{ext}"
                path = os.path.join(upload_dir, name)
                f.save(path)
                paths.append('work_photos/' + name)
    if paths:
        existing = (c.work_photos or '').split(',')
        existing = [x.strip() for x in existing if x.strip()]
        c.work_photos = ','.join(existing + paths)
        db.session.add(c)
    db.session.commit()
    flash('Complaint updated.', 'success')
    return redirect(url_for('admin_dashboard', view='complaints'))

@app.route('/admin/complaint/<int:cid>/remove', methods=['POST'])
@login_required
def remove_complaint(cid):
    if not is_ward_admin():
        flash('Not allowed.', 'danger')
        return redirect(url_for('citizen_dashboard'))
    c = Complaint.query.get_or_404(cid)
    if c.ward_id != current_user.ward_id:
        flash('Not allowed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(c)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True})
    flash('Complaint removed.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    # Use forward slashes so URLs work on all systems
    filename = filename.replace('\\', '/').lstrip('/')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)