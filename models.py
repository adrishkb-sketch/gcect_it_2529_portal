from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

# ----------------- USER MODELS -----------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    group = db.Column(db.String(10))
    is_cr = db.Column(db.Boolean, default=False)

    attendance_records = db.relationship('AttendanceRecord', back_populates='student', cascade='all, delete-orphan')
    submissions = db.relationship('AssignmentSubmission', back_populates='student', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Student {self.roll} - {self.name}>"

class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prof_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))

    attendance_sessions = db.relationship('AttendanceSession', back_populates='professor', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', back_populates='professor', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Professor {self.prof_id} - {self.name}>"

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ----------------- SUBJECT MODEL -----------------
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    subject_type = db.Column(db.String(20))  # "Theory" or "Practical"

    attendance_sessions = db.relationship('AttendanceSession', back_populates='subject', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', back_populates='subject', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Subject {self.name} ({self.subject_type})>"

# ----------------- ATTENDANCE MODELS -----------------
class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subject_type = db.Column(db.String(20), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    recorded_by_cr_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    group_flag = db.Column(db.String(10), nullable=False, default='ALL')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = db.relationship('Subject', back_populates='attendance_sessions')
    professor = db.relationship('Professor', back_populates='attendance_sessions')
    recorded_by_cr = db.relationship('Student', foreign_keys=[recorded_by_cr_id])
    records = db.relationship('AttendanceRecord', back_populates='session', cascade='all, delete-orphan', lazy='dynamic')

    def mark_student(self, student, present: bool, note: str = None):
        rec = AttendanceRecord.query.filter_by(session_id=self.id, student_id=student.id).first()
        if not rec:
            rec = AttendanceRecord(session=self, student=student, present=bool(present), note=note)
            db.session.add(rec)
        else:
            rec.present = bool(present)
            if note is not None:
                rec.note = note
        return rec

    def get_report(self):
        rows = []
        for rec in self.records.order_by(AttendanceRecord.id).all():
            rows.append({
                "student_id": rec.student.id,
                "roll": rec.student.roll,
                "name": rec.student.name,
                "group": rec.student.group,
                "present": rec.present,
                "note": rec.note
            })
        return rows

    def __repr__(self):
        return f"<AttendanceSession {self.id} {self.subject.name} {self.date}>"

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    present = db.Column(db.Boolean, nullable=False, default=False)
    note = db.Column(db.String(200), nullable=True)

    session = db.relationship('AttendanceSession', back_populates='records')
    student = db.relationship('Student', back_populates='attendance_records')

# ----------------- ASSIGNMENT MODELS -----------------
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    assignment_type = db.Column(db.String(20), nullable=False)  # 'Online' or 'Offline'
    document = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', back_populates='assignments')
    professor = db.relationship('Professor', back_populates='assignments')
    submissions = db.relationship('AssignmentSubmission', back_populates='assignment', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Assignment {self.title} ({self.assignment_type})>"

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Submitted', 'Completed', 'Missed'
    submission_file = db.Column(db.String(200), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)

    assignment = db.relationship('Assignment', back_populates='submissions')
    student = db.relationship('Student', back_populates='submissions')

    def update_status(self):
        today = date.today()
        if self.status in ['Submitted', 'Completed']:
            return self.status
        if self.assignment.due_date < today:
            self.status = 'Missed'
        elif self.submission_file is None:
            self.status = 'Pending'
        return self.status

    def __repr__(self):
        return f"<Submission {self.student.roll} - {self.assignment.title} - {self.status}>"

# ----------------- ANNOUNCEMENT MODEL -----------------
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(200))  # optional file attachment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AnnouncementGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(200))  # optional file upload
    group = db.Column(db.String(10), nullable=False)  # "A" or "B"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AnnouncementGroup {self.title} ({self.group})>"
