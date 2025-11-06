from flask import Flask, render_template, redirect, url_for, flash, session, request
from models import db, Student, Professor, Admin, Subject, AttendanceSession, AttendanceRecord, AnnouncementGroup
from forms import (
    StudentLoginForm, ProfessorLoginForm, AdminLoginForm,
    StudentForm, SubjectForm, ProfessorForm
)
from werkzeug.security import generate_password_hash

from flask import send_file


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gcect_it_25_29.db'
app.config['SECRET_KEY'] = 'supersecretkey'
db.init_app(app)
import os

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ensure folder exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from flask import session
from models import Student

def get_current_student():
    # Use roll because your login sets session['student_roll']
    roll = session.get('student_roll')
    if not roll:
        return None
    return Student.query.filter_by(roll=roll).first()


# ------------------ HOME ------------------
@app.route('/')
def home():
    return redirect(url_for('login_student'))


# ------------------ STUDENT LOGIN ------------------
@app.route('/login_student', methods=['GET', 'POST'])
def login_student():
    form = StudentLoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(roll=form.roll.data).first()
        if student and student.check_password(form.password.data):
            session['student_roll'] = student.roll
            return redirect(url_for('dashboard_student'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login_student.html', form=form)


from models import (
    db, Student, AttendanceRecord, Assignment, AssignmentSubmission
)
from sqlalchemy import func

@app.route('/dashboard_student')
def dashboard_student():
    roll = session.get('student_roll')
    if not roll:
        return redirect(url_for('login_student'))

    student = Student.query.filter_by(roll=roll).first()
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('login_student'))

    # --- Attendance Stats ---
    total_classes = AttendanceRecord.query.filter_by(student_id=student.id).count()
    attended_classes = AttendanceRecord.query.filter_by(student_id=student.id, present=True).count()
    attendance_percentage = round((attended_classes / total_classes) * 100, 1) if total_classes > 0 else 0

    # --- Assignment Stats ---
    total_assignments = Assignment.query.count()
    completed_assignments = AssignmentSubmission.query.filter_by(student_id=student.id, status='Submitted').count()

    return render_template(
        'dashboard_student.html',
        student=student,
        attendance_percentage=attendance_percentage,
        attended_classes=attended_classes,
        total_classes=total_classes,
        completed_assignments=completed_assignments,
        total_assignments=total_assignments
    )



# ------------------ PROFESSOR LOGIN ------------------
@app.route('/login_professor', methods=['GET', 'POST'])
def login_professor():
    form = ProfessorLoginForm()
    if form.validate_on_submit():
        prof = Professor.query.filter_by(prof_id=form.prof_id.data).first()
        if prof and prof.check_password(form.password.data):
            session['prof_id'] = prof.prof_id
            return redirect(url_for('dashboard_professor'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login_professor.html', form=form)


@app.route('/dashboard_professor')
def dashboard_professor():
    prof_id = session.get('prof_id')
    if not prof_id:
        return redirect(url_for('login_professor'))
    prof = Professor.query.filter_by(prof_id=prof_id).first()
    return render_template('dashboard_professor.html', professor=prof)


# ------------------ ADMIN LOGIN ------------------
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            session['admin_username'] = admin.username
            return redirect(url_for('dashboard_admin'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login_admin.html', form=form)


@app.route('/dashboard_admin')
def dashboard_admin():
    username = session.get('admin_username')
    if not username:
        return redirect(url_for('login_admin'))
    admin = Admin.query.filter_by(username=username).first()
    return render_template('dashboard_admin.html', admin=admin)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login_student'))


# ------------------ MANAGE STUDENTS ------------------
@app.route('/admin/manage_students', methods=['GET', 'POST'])
def manage_students():
    form = StudentForm()
    students = Student.query.all()

    if form.validate_on_submit():
        student = Student.query.filter_by(roll=form.roll.data).first()
        if student:
            student.name = form.name.data
            student.group = form.group.data
            student.is_cr = form.is_cr.data
            if form.password.data:
                student.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Student updated successfully!', 'success')
        else:
            new_student = Student(
                name=form.name.data,
                roll=form.roll.data,
                group=form.group.data,
                is_cr=form.is_cr.data,
                password_hash=generate_password_hash(form.password.data)
            )
            db.session.add(new_student)
            db.session.commit()
            flash('Student added successfully!', 'success')
        return redirect(url_for('manage_students'))

    return render_template('manage_students.html', form=form, students=students)


@app.route('/admin/delete_student/<int:student_id>')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('manage_students'))


@app.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)
    if request.method == 'POST' and form.validate_on_submit():
        student.name = form.name.data
        student.roll = form.roll.data
        student.group = form.group.data
        student.is_cr = form.is_cr.data
        if form.password.data:
            student.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('manage_students'))
    return render_template('manage_students.html', form=form, students=Student.query.all())


# ------------------ MANAGE SUBJECTS ------------------
@app.route('/admin/manage_subjects', methods=['GET', 'POST'])
def manage_subjects():
    form = SubjectForm()
    subjects = Subject.query.all()

    subject_id = request.args.get('subject_id')
    subject = Subject.query.get(subject_id) if subject_id else None

    if subject and request.method == 'GET':
        form.name.data = subject.name
        form.subject_type.data = subject.subject_type

    if form.validate_on_submit():
        if subject:
            subject.name = form.name.data
            subject.subject_type = form.subject_type.data
            flash('Subject updated successfully!', 'success')
        else:
            new_subject = Subject(name=form.name.data, subject_type=form.subject_type.data)
            db.session.add(new_subject)
            flash('Subject added successfully!', 'success')
        db.session.commit()
        return redirect(url_for('manage_subjects'))

    return render_template('manage_subjects.html', form=form, subjects=subjects)


@app.route('/admin/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('manage_subjects'))


@app.route('/admin/edit_subject/<int:subject_id>')
def edit_subject(subject_id):
    return redirect(url_for('manage_subjects', subject_id=subject_id))


# ------------------ MANAGE PROFESSORS (Cleaned) ------------------
@app.route('/admin/manage_professors', methods=['GET', 'POST'])
def manage_professors():
    form = ProfessorForm()
    professors = Professor.query.all()

    if form.validate_on_submit():
        prof = Professor.query.filter_by(prof_id=form.prof_id.data).first()
        if prof:
            # Update existing professor
            prof.name = form.name.data
            if form.password.data:
                prof.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Professor updated successfully!', 'success')
        else:
            # Add new professor
            new_prof = Professor(
                name=form.name.data,
                prof_id=form.prof_id.data,
                password_hash=generate_password_hash(form.password.data)
            )
            db.session.add(new_prof)
            db.session.commit()
            flash('Professor added successfully!', 'success')

        return redirect(url_for('manage_professors'))

    return render_template('manage_professors.html', form=form, professors=professors)


@app.route('/admin/delete_professor/<int:professor_id>')
def delete_professor(professor_id):
    professor = Professor.query.get_or_404(professor_id)
    db.session.delete(professor)
    db.session.commit()
    flash('Professor deleted successfully!', 'success')
    return redirect(url_for('manage_professors'))


@app.route('/admin/edit_professor/<int:professor_id>', methods=['GET', 'POST'])
def edit_professor(professor_id):
    professor = Professor.query.get_or_404(professor_id)
    form = ProfessorForm(obj=professor)
    professors = Professor.query.all()

    if form.validate_on_submit():
        professor.name = form.name.data
        professor.prof_id = form.prof_id.data
        if form.password.data:
            professor.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Professor updated successfully!', 'success')
        return redirect(url_for('manage_professors'))

    return render_template('manage_professors.html', form=form, professors=professors)

from flask import abort, jsonify, make_response
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ----------------------------
# STUDENT: View Attendance
# ----------------------------
# Route for students (uses current logged-in student roll from session).
# Admins can open /attendance/view/<int:student_id> to view specific student.
@app.route('/attendance/view')
@app.route('/attendance/view/<int:student_id>')
def attendance_view(student_id=None):
    # if student_id provided (admin/prof access), use it; otherwise use logged-in student
    if student_id is None:
        roll = session.get('student_roll')
        if not roll:
            flash("Please login as a student to view attendance.", "warning")
            return redirect(url_for('login_student'))
        student = Student.query.filter_by(roll=roll).first()
    else:
        student = Student.query.get_or_404(student_id)

    # gather student's attendance records joined with session
    records = (
        AttendanceRecord.query
        .filter_by(student_id=student.id)
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .order_by(AttendanceSession.date.desc())
        .all()
    )
    return render_template('attendance_view.html', student=student, records=records)


# ----------------------------
# CR: Mark / Upload Attendance
# ----------------------------
# CR visits /attendance/mark and we identify CR from session['student_roll'] (or cr_id param)
@app.route('/attendance/mark', methods=['GET', 'POST'])
@app.route('/attendance/mark/<int:cr_id>', methods=['GET', 'POST'])
def attendance_mark(cr_id=None):
    # identify CR user
    if cr_id:
        cr = Student.query.get_or_404(cr_id)
    else:
        roll = session.get('student_roll')
        if not roll:
            flash("Please login as CR to mark attendance.", "warning")
            return redirect(url_for('login_student'))
        cr = Student.query.filter_by(roll=roll).first()

    if not cr or not cr.is_cr:
        flash("Only CRs can upload attendance from this page.", "danger")
        return redirect(url_for('dashboard_student'))

    professors = Professor.query.order_by(Professor.name).all()
    subjects = Subject.query.order_by(Subject.name).all()

    # default students listing (all students). We'll filter by group when processing form
    students = Student.query.order_by(Student.roll).all()

    if request.method == 'POST':
        # read form fields
        try:
            subject_id = int(request.form['subject'])
        except Exception:
            flash("Please select a valid subject.", "danger")
            return redirect(request.url)

        try:
            professor_id = int(request.form['professor'])
        except Exception:
            flash("Please select a valid professor.", "danger")
            return redirect(request.url)

        date_str = request.form.get('date')
        if not date_str:
            flash("Please select a date.", "danger")
            return redirect(request.url)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(request.url)

        subject_type = request.form.get('subject_type', '').strip()
        group_choice = request.form.get('group_choice', 'ALL')  # A / B / ALL

        # selected present students (posted as list of student ids)
        present_ids = request.form.getlist('present_students')
        present_ids = set([int(x) for x in present_ids]) if present_ids else set()

        # Check if a session for same subject/professor/date/group already exists:
        session_obj = AttendanceSession.query.filter_by(
            subject_id=subject_id,
            professor_id=professor_id,
            date=date_obj,
            group_flag=group_choice
        ).first()

        if session_obj:
            # overwrite existing records: delete and recreate
            AttendanceRecord.query.filter_by(session_id=session_obj.id).delete()
            db.session.commit()
        else:
            session_obj = AttendanceSession(
                subject_id=subject_id,
                professor_id=professor_id,
                date=date_obj,
                subject_type=subject_type,
                recorded_by_cr_id=cr.id,
                group_flag=group_choice
            )
            db.session.add(session_obj)
            db.session.commit()

        # determine student list to record for (respecting group_choice and subject_type)
        if subject_type.lower() == 'practical' and group_choice in ('A', 'B'):
            students_to_mark = Student.query.filter_by(group=group_choice).all()
        else:
            students_to_mark = Student.query.all()

        # create AttendanceRecord rows
        to_add = []
        for s in students_to_mark:
            present = s.id in present_ids
            rec = AttendanceRecord(session_id=session_obj.id, student_id=s.id, present=present)
            to_add.append(rec)
        db.session.bulk_save_objects(to_add)
        db.session.commit()

        flash('Attendance uploaded successfully.', 'success')
        return redirect(url_for('attendance_mark', cr_id=cr.id))

    # GET -> render form
    return render_template('attendance_mark.html', cr=cr, professors=professors, subjects=subjects, students=students)


# ----------------------------
# PROFESSOR: Attendance Report (search & PDF download)
# ----------------------------
@app.route('/attendance/report', methods=['GET', 'POST'])
def attendance_report():
    professors = Professor.query.order_by(Professor.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    matched_sessions = []

    if request.method == 'POST':
        professor_id = request.form.get('professor')
        subject_id = request.form.get('subject')
        date_str = request.form.get('date')
        subject_type = request.form.get('subject_type')

        # basic validation
        try:
            professor_id = int(professor_id)
            subject_id = int(subject_id)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            flash("Please select valid professor, subject and date.", "danger")
            return render_template('attendance_report.html', professors=professors, subjects=subjects, sessions=matched_sessions)

        # find matching sessions (could be multiple if different group flags)
        matched_sessions = AttendanceSession.query.filter_by(
            professor_id=professor_id,
            subject_id=subject_id,
            date=date_obj,
            subject_type=subject_type
        ).order_by(AttendanceSession.group_flag).all()

        # If download requested -> generate PDF
        if 'download' in request.form:
            # generate PDF bytes
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            y = 750
            for s in matched_sessions:
                subj = Subject.query.get(s.subject_id)
                prof = Professor.query.get(s.professor_id)
                p.setFont("Helvetica-Bold", 11)
                p.drawString(50, y, f"{subj.name} ({s.subject_type}) — Prof: {prof.name} — Date: {s.date} — Group: {s.group_flag}")
                y -= 18
                p.setFont("Helvetica", 10)
                for r in s.records.order_by(AttendanceRecord.id).all():
                    st = Student.query.get(r.student_id)
                    status = "Present" if r.present else "Absent"
                    line = f"{st.roll}  {st.name}  —  {status}"
                    p.drawString(60, y, line)
                    y -= 14
                    if y < 60:
                        p.showPage()
                        y = 750
                y -= 10

            p.save()
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='attendance_report.pdf', mimetype='application/pdf')

    return render_template('attendance_report.html', professors=professors, subjects=subjects, sessions=matched_sessions)


# ----------------------------
# ADMIN: Edit Attendance
# ----------------------------
@app.route('/attendance/edit', methods=['GET', 'POST'])
def attendance_edit():
    # only allow access if logged-in admin
    username = session.get('admin_username')
    if not username:
        flash("Admin login required.", "warning")
        return redirect(url_for('login_admin'))

    professors = Professor.query.order_by(Professor.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    records = []
    session_obj = None

    if request.method == 'POST':
        # first button click to search session
        if 'search' in request.form:
            try:
                professor_id = int(request.form.get('professor'))
                subject_id = int(request.form.get('subject'))
                date_obj = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            except Exception:
                flash("Please provide valid professor, subject and date.", "danger")
                return render_template('attendance_edit.html', professors=professors, subjects=subjects, records=records)

            session_obj = AttendanceSession.query.filter_by(
                professor_id=professor_id,
                subject_id=subject_id,
                date=date_obj
            ).first()

            if not session_obj:
                flash("No attendance session found for the given details.", "info")
            else:
                records = AttendanceRecord.query.filter_by(session_id=session_obj.id).all()

            return render_template('attendance_edit.html', professors=professors, subjects=subjects, records=records, session=session_obj)

        # update button to save edited statuses
        if 'update' in request.form:
            session_id = int(request.form.get('session_id'))
            session_obj = AttendanceSession.query.get_or_404(session_id)
            for rec in session_obj.records:
                new_val = request.form.get(f'status_{rec.id}')
                rec.present = True if new_val == 'Present' else False
            db.session.commit()
            flash("Attendance updated successfully.", "success")
            return redirect(url_for('attendance_edit'))

    return render_template('attendance_edit.html', professors=professors, subjects=subjects, records=records, session=session_obj)

from flask import render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os, zipfile
from models import Assignment, AssignmentSubmission, Student, Professor
from forms import AssignmentCreateForm, AssignmentMarkForm, AssignmentEditForm
from datetime import date

# -------- Create Assignment --------
# -------- Create Assignment --------
@app.route('/assignments_create', methods=['GET','POST'])
def assignments_create():
    form = AssignmentCreateForm()

    # Populate the dropdowns dynamically from the database
    form.subject.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.professor.choices = [(p.id, p.name) for p in Professor.query.order_by(Professor.name).all()]

    if form.validate_on_submit():
        filename = None
        if form.document.data:
            filename = secure_filename(form.document.data.filename)
            # Save in uploads folder (make sure folder exists)
            form.document.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_assignment = Assignment(
            title=form.title.data,
            subject_id=form.subject.data,
            professor_id=form.professor.data,
            due_date=form.due_date.data,
            assignment_type=form.assignment_type.data,
            document=filename
        )
        db.session.add(new_assignment)
        db.session.commit()
        flash("Assignment created successfully!", "success")
        return redirect(url_for('assignments_create'))

    return render_template('assignments_create.html', form=form)



# -------- Student View Assignments --------
@app.route('/assignments_view')
def assignments_view():
    student = get_current_student()
    if not student:
        flash("Please login as a student.", "warning")
        return redirect(url_for('login_student'))

    assignments = Assignment.query.order_by(Assignment.due_date.desc()).all()
    submissions = {sub.assignment_id: sub for sub in AssignmentSubmission.query.filter_by(student_id=student.id).all()}

    return render_template('assignments_view.html', assignments=assignments, submissions=submissions, student=student, today=date.today())
from flask import render_template, request, redirect, url_for, flash
from models import Assignment, AssignmentSubmission, Student
from forms import AssignmentEditForm


@app.route('/assignments/<int:assignment_id>/upload', methods=['POST'])
def upload_assignment(assignment_id):
    student = get_current_student()
    if not student:
        flash("Please login as a student.", "warning")
        return redirect(url_for('login_student'))

    assignment = Assignment.query.get_or_404(assignment_id)

    if 'file' not in request.files:
        flash("No file part in request.", "danger")
        return redirect(url_for('assignments_view'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('assignments_view'))

    # Save file in uploads folder
    filename = secure_filename(f"{student.roll}_{assignment.id}_{file.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Record in database
    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id, student_id=student.id
    ).first()

    if not submission:
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=student.id,
            submission_file=file_path,
            status="Submitted"
        )
        db.session.add(submission)
    else:
        # Update existing submission
        submission.submission_file = file_path
        submission.status = "Submitted"

    db.session.commit()
    flash("Assignment uploaded successfully!", "success")
    return redirect(url_for('assignments_view'))



@app.route('/assignments_edit', methods=['GET', 'POST'])
def assignments_edit():
    form = AssignmentEditForm()
    professors = Professor.query.order_by(Professor.name).all()
    subjects = []
    assignments = []
    students = []

    selected_professor_id = request.form.get('professor_id', type=int)
    selected_subject_id = request.form.get('subject_id', type=int)
    selected_assignment_id = request.form.get('assignment_id', type=int)

    # If professor selected, populate subjects and assignments
    if selected_professor_id:
        # Subjects for this professor's offline assignments
        subjects = Subject.query.join(Assignment).filter(
            Assignment.professor_id == selected_professor_id,
            Assignment.assignment_type == 'Offline'
        ).distinct().all()

        # Assignments for this professor
        assignments = Assignment.query.filter_by(
            professor_id=selected_professor_id,
            assignment_type='Offline'
        ).all()

    # If assignment selected, populate students and their status
    if selected_assignment_id:
        assignment = Assignment.query.get(selected_assignment_id)
        students = Student.query.order_by(Student.roll).all()
        # attach status for each student
        for s in students:
            sub = AssignmentSubmission.query.filter_by(
                student_id=s.id,
                assignment_id=assignment.id
            ).first()
            s.status = sub.status if sub else 'Pending'

    # Handle update of statuses
    if request.method == 'POST' and 'update' in request.form:
        assignment_id = selected_assignment_id
        assignment = Assignment.query.get(assignment_id)
        for s in Student.query.all():
            status = request.form.get(f'status_{s.id}')
            sub = AssignmentSubmission.query.filter_by(
                assignment_id=assignment.id,
                student_id=s.id
            ).first()
            if not sub:
                sub = AssignmentSubmission(
                    assignment_id=assignment.id,
                    student_id=s.id,
                    status=status
                )
                db.session.add(sub)
            else:
                sub.status = status
        db.session.commit()
        flash("Statuses updated successfully!", "success")
        return redirect(url_for('assignments_edit'))

    return render_template(
        'assignments_edit.html',
        form=form,
        professors=professors,
        subjects=subjects,
        assignments=assignments,
        students=students,
        selected_professor_id=selected_professor_id,
        selected_subject_id=selected_subject_id,
        selected_assignment_id=selected_assignment_id
    )


# -------- Offline Assignment Marking by CR --------
@app.route('/assignments_mark', methods=['GET','POST'])
def assignments_mark():
    form = AssignmentMarkForm()
    form.professor.choices = [(p.id, p.name) for p in Professor.query.all()]
    form.assignment.choices = []

    assignments = []  # <-- initialize here
    selected_prof_id = None
    selected_assignment = None
    students = []

    if request.method == 'POST':
        prof_val = request.form.get('professor')
        assign_val = request.form.get('assignment')

        # Only convert to int if value is not empty
        if prof_val:
            selected_prof_id = int(prof_val)
            assignments = Assignment.query.filter_by(professor_id=selected_prof_id, assignment_type='Offline').all()
            form.assignment.choices = [(a.id, a.title) for a in assignments]

        if assign_val:
            assignment_id = int(assign_val)
            selected_assignment = Assignment.query.get(assignment_id)
            students = Student.query.all()
            # Attach current status for each student
            for s in students:
                sub = AssignmentSubmission.query.filter_by(student_id=s.id, assignment_id=assignment_id).first()
                s.status = sub.status if sub else 'Pending'

        # Update statuses
        if 'update' in request.form and selected_assignment:
            for s in students:
                status = request.form.get(f'status_{s.id}')
                sub = AssignmentSubmission.query.filter_by(assignment_id=selected_assignment.id, student_id=s.id).first()
                if not sub:
                    sub = AssignmentSubmission(assignment_id=selected_assignment.id, student_id=s.id, status=status)
                    db.session.add(sub)
                else:
                    sub.status = status
            db.session.commit()
            flash("Statuses updated successfully!", "success")
            return redirect(url_for('assignments_mark'))

    return render_template('assignments_mark.html', form=form, professors=form.professor.choices,
                           assignments=assignments, students=students,
                           selected_prof_id=selected_prof_id, selected_assignment=selected_assignment)


# -------- Assignment Responses (Download ZIP) --------
@app.route('/assignments_response', methods=['GET','POST'])
def assignments_response():
    professors = Professor.query.order_by(Professor.name).all()
    selected_professor_id = request.form.get('professor_id', type=int)
    selected_assignment_id = request.form.get('assignment_id', type=int)
    selected_assignment = None
    assignments = []

    # Populate assignments based on professor
    if selected_professor_id:
        assignments = Assignment.query.filter_by(professor_id=selected_professor_id).order_by(Assignment.title).all()

    # If download requested
    if request.method == 'POST' and selected_assignment_id:
        selected_assignment = Assignment.query.get(selected_assignment_id)
        submissions = AssignmentSubmission.query.filter_by(assignment_id=selected_assignment_id).all()

        # ZIP file creation
        zip_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"responses_{selected_assignment.id}.zip")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for sub in submissions:
                if sub.submission_file and os.path.exists(sub.submission_file):
                    # Store file inside ZIP with student roll prefix
                    zipf.write(sub.submission_file, arcname=os.path.basename(sub.submission_file))

        return send_file(zip_filename, as_attachment=True)

    return render_template(
        'assignments_response.html',
        professors=professors,
        assignments=assignments,
        selected_professor_id=selected_professor_id,
        selected_assignment_id=selected_assignment_id,
        selected_assignment=selected_assignment,
        role='professor' if 'prof_id' in session else 'admin'
    )
from flask import request, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
from models import Announcement

@app.route('/admin/announcement_create', methods=['GET','POST'])
def announcement_create():
    # Ensure only admin can access
    username = session.get('admin_username')
    if not username:
        flash("Admin login required.", "warning")
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('file')

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        announcement = Announcement(
            title=title,
            description=description,
            filename=filename
        )
        db.session.add(announcement)
        db.session.commit()
        flash("Announcement posted successfully!", "success")
        return redirect(url_for('announcement_create'))

    return render_template('announcement_create.html')
from flask import send_from_directory

@app.route('/announcement_view')
def announcement_view():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcement_view.html', announcements=announcements)

# Route to download attachments
@app.route('/announcement_download/<int:announcement_id>')
def announcement_download(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    if not ann.filename:
        flash("No file attached.", "warning")
        return redirect(url_for('announcement_view'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], ann.filename, as_attachment=True)
# CR: Create group announcement
@app.route('/announcement_group_create', methods=['GET', 'POST'])
def announcement_group_create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        group = request.form['group']
        file = request.files.get('file')

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        new_announcement = AnnouncementGroup(
            title=title,
            description=description,
            group=group,
            filename=filename
        )
        db.session.add(new_announcement)
        db.session.commit()

        # ✅ FIXED LINE BELOW
        return redirect(url_for('announcement_group_view', group=group))

    return render_template('announcement_group_create.html')


# Student: View group announcements for their group only
@app.route("/announcement_group_view/<group>")
def announcement_group_view(group):
    announcements = AnnouncementGroup.query.filter_by(group=group).order_by(AnnouncementGroup.created_at.desc()).all()
    return render_template("announcement_group_view.html", announcements=announcements, group=group)


    return render_template('announcement_group_view.html', announcements=announcements)
@app.route('/announcement_group_download/<int:announcement_id>')
def announcement_group_download(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    student = get_current_student()
    if not student:
        flash("Please login first.", "warning")
        return redirect(url_for('login_student'))

    # ensure the student is allowed to download (belong to the group)
    if ann.group != student.group:
        flash("You are not authorized to download this file.", "danger")
        return redirect(url_for('announcement_group_view'))

    if not ann.filename:
        flash("No attachment for this announcement.", "info")
        return redirect(url_for('announcement_group_view'))

    return send_from_directory(app.config['GROUP_ANNOUNCEMENTS_FOLDER'], ann.filename, as_attachment=True)

# ----------------------------
# PROFESSOR: Student Reports
# ----------------------------
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    # only accessible to logged-in professors
    prof_id = session.get('prof_id')
    if not prof_id:
        flash("Please login as a professor to view reports.", "warning")
        return redirect(url_for('login_professor'))

    # all students to populate dropdown
    students = Student.query.order_by(Student.roll).all()
    selected_student = None

    # overall summaries
    attendance_summary = None
    assignment_summary = None

    # per-subject breakdown lists
    per_subject_attendance = []    # list of dicts: {subject_id, subject_name, present, total}
    per_subject_assignments = []   # list of dicts: {subject_id, subject_name, submitted, total}

    if request.method == 'POST':
        try:
            student_id = int(request.form.get('student_id'))
        except Exception:
            flash("Please select a valid student.", "danger")
            return render_template('reports.html', students=students)

        selected_student = Student.query.get_or_404(student_id)

        # ---- Overall attendance ----
        total_records = AttendanceRecord.query.filter_by(student_id=selected_student.id).count()
        attended = AttendanceRecord.query.filter_by(student_id=selected_student.id, present=True).count()
        attendance_summary = {
            'attended': attended,
            'total': total_records
        }

        # ---- Overall assignments ----
        total_assignments = Assignment.query.count()
        submitted_assignments = AssignmentSubmission.query.filter_by(student_id=selected_student.id).filter(
            AssignmentSubmission.status.in_(['Submitted','Completed'])
        ).count()
        assignment_summary = {
            'submitted': submitted_assignments,
            'total': total_assignments
        }

        # ---- Per-subject attendance ----
        # For each subject that has at least one session, compute student's present/total for that subject.
        subjects = Subject.query.order_by(Subject.name).all()
        for subj in subjects:
            # total attendance records for this student in sessions of this subject
            subj_total = AttendanceRecord.query.join(
                AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id
            ).filter(
                AttendanceRecord.student_id == selected_student.id,
                AttendanceSession.subject_id == subj.id
            ).count()

            if subj_total == 0:
                # skip subjects with no attendance records for this student
                continue

            subj_present = AttendanceRecord.query.join(
                AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id
            ).filter(
                AttendanceRecord.student_id == selected_student.id,
                AttendanceSession.subject_id == subj.id,
                AttendanceRecord.present == True
            ).count()

            per_subject_attendance.append({
                'subject_id': subj.id,
                'subject_name': subj.name,
                'present': subj_present,
                'total': subj_total
            })

        # ---- Per-subject assignments ----
        for subj in subjects:
            subj_total_assignments = Assignment.query.filter_by(subject_id=subj.id).count()
            if subj_total_assignments == 0:
                continue
            subj_submitted = AssignmentSubmission.query.join(
                Assignment, Assignment.id == AssignmentSubmission.assignment_id
            ).filter(
                AssignmentSubmission.student_id == selected_student.id,
                Assignment.subject_id == subj.id,
                AssignmentSubmission.status.in_(['Submitted','Completed'])
            ).count()

            per_subject_assignments.append({
                'subject_id': subj.id,
                'subject_name': subj.name,
                'submitted': subj_submitted,
                'total': subj_total_assignments
            })

    return render_template(
        'reports.html',
        students=students,
        selected_student=selected_student,
        attendance_summary=attendance_summary,
        assignment_summary=assignment_summary,
        per_subject_attendance=per_subject_attendance,
        per_subject_assignments=per_subject_assignments
    )
@app.route('/delete_everything')
def delete_everything():
    from models import (
        db,
        AttendanceRecord,
        AttendanceSession,
        Assignment,
        AssignmentSubmission,
        Announcement,
        AnnouncementGroup
    )

    try:
        # Delete attendance-related data
        AttendanceRecord.query.delete()
        AttendanceSession.query.delete()

        # Delete assignment-related data
        AssignmentSubmission.query.delete()
        Assignment.query.delete()

        # Delete announcements
        Announcement.query.delete()
        AnnouncementGroup.query.delete()

        # Commit all changes
        db.session.commit()
        flash("✅ All attendance, assignments, and announcements have been deleted successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Error deleting data: {str(e)}", "error")

    return redirect(url_for('dashboard_admin', admin_id=session.get('admin_id')))


# ------------------ MAIN ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
