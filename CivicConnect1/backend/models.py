from datetime import datetime

from flask_login import UserMixin

from extensions import db


class Ward(db.Model):
    __tablename__ = "wards"

    id = db.Column(db.Integer, primary_key=True)
    ward_number = db.Column(db.Integer, nullable=False, unique=True)
    ward_code = db.Column(db.String(50), nullable=False, unique=True)

    users = db.relationship("User", back_populates="ward", lazy=True)
    complaints = db.relationship("Complaint", back_populates="ward", lazy=True)
    projects = db.relationship("Project", back_populates="ward", lazy=True)
    announcements = db.relationship(
        "Announcement", back_populates="ward", lazy=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Ward {self.ward_number} ({self.ward_code})>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="citizen")

    ward_id = db.Column(db.Integer, db.ForeignKey("wards.id"), nullable=False)
    ward = db.relationship("Ward", back_populates="users")

    complaints = db.relationship("Complaint", back_populates="user", lazy=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User {self.email} ({self.role})>"


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey("wards.id"), nullable=False)

    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))

    status = db.Column(db.String(50), nullable=False, default="Submitted")
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    user = db.relationship("User", back_populates="complaints")
    ward = db.relationship("Ward", back_populates="complaints")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Complaint {self.id} - {self.status}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    ward_id = db.Column(db.Integer, db.ForeignKey("wards.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    contractor_name = db.Column(db.String(150))
    budget = db.Column(db.Numeric(12, 2))

    start_date = db.Column(db.Date)
    deadline = db.Column(db.Date)

    status = db.Column(db.String(50), nullable=False, default="Planned")
    progress_percentage = db.Column(db.Integer, nullable=False, default=0)

    image_path = db.Column(db.String(255))

    ward = db.relationship("Ward", back_populates="projects")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Project {self.title} ({self.status})>"


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    ward_id = db.Column(db.Integer, db.ForeignKey("wards.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(50), nullable=False, default="Normal")

    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    ward = db.relationship("Ward", back_populates="announcements")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Announcement {self.title} ({self.priority})>"


def create_sample_data() -> None:
    """Create one ward and one ward admin for demo."""
    from werkzeug.security import generate_password_hash

    if not Ward.query.first():
        ward = Ward(ward_number=1, ward_code="WARD1")
        db.session.add(ward)
        db.session.commit()
    else:
        ward = Ward.query.first()

    admin = User.query.filter_by(role="ward_admin").first()
    if not admin:
        admin = User(
            name="Ward Admin",
            email="admin@civicconnect.local",
            password_hash=generate_password_hash("admin123"),
            role="ward_admin",
            ward_id=ward.id,
        )
        db.session.add(admin)
        db.session.commit()

