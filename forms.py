from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

# ---------------- Existing Login Forms ----------------
class StudentLoginForm(FlaskForm):
    roll = StringField('Roll Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ProfessorLoginForm(FlaskForm):
    prof_id = StringField('Professor ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# ---------------- Existing Admin Forms ----------------
class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    roll = StringField('Roll', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password')  # optional for editing
    group = SelectField('Group', choices=[('A', 'A'), ('B', 'B')], validators=[DataRequired()])
    is_cr = BooleanField('CR?')
    submit = SubmitField('Submit')


class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired(), Length(max=100)])
    subject_type = SelectField('Type', choices=[('Theory', 'Theory'), ('Practical', 'Practical')], validators=[DataRequired()])
    submit = SubmitField('Submit')


# ---------------- UPDATED: Professor Management Form (NO subjects) ----------------
class ProfessorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    prof_id = StringField('Professor ID', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password')  # optional for editing
    submit = SubmitField('Submit')
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, FileField, SubmitField
from wtforms.validators import DataRequired

class AssignmentCreateForm(FlaskForm):
    title = StringField("Assignment Title", validators=[DataRequired()])
    subject = SelectField("Subject", coerce=int, validators=[DataRequired()])
    professor = SelectField("Professor", coerce=int, validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[DataRequired()])
    assignment_type = SelectField("Type", choices=[("Online", "Online"), ("Offline", "Offline")], validators=[DataRequired()])
    document = FileField("Upload Document")
    submit = SubmitField("Create Assignment")



class AssignmentMarkForm(FlaskForm):
    professor = SelectField('Professor', coerce=int, validators=[DataRequired()])
    assignment = SelectField('Assignment', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Status')


class AssignmentEditForm(FlaskForm):
    status = SelectField('Status', choices=[('Pending','Pending'), ('Submitted','Submitted'), ('Completed','Completed'), ('Missed','Missed')], validators=[DataRequired()])
    submit = SubmitField('Update Submission')
