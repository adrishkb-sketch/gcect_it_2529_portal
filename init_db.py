from app import app, db
from models import Student, Professor, Admin, Subject

with app.app_context():
    # Drop all just in case
    db.drop_all()
    # Create tables
    db.create_all()
    print("✅ Tables created successfully!")

    # Sample Students
    students = [
        ("IT2501", "Riya Sharma", "A", False),
        ("IT2502", "Aditya Sen", "A", True),
        ("IT2503", "Soham Das", "B", False),
        ("IT2504", "Priya Roy", "B", False),
    ]
    for i, (roll, name, group, is_cr) in enumerate(students, start=1):
        s = Student(roll=roll, name=name, group=group, is_cr=is_cr)
        s.set_password(f"stud{str(i).zfill(2)}login")
        db.session.add(s)

    # Professors
    profs = [
        ("P101", "Dr. Arindam Banerjee"),
        ("P102", "Dr. Debanjan Dey"),
    ]
    for i, (pid, name) in enumerate(profs, start=1):
        p = Professor(prof_id=pid, name=name)
        p.set_password(f"prof{str(i).zfill(2)}login")
        db.session.add(p)

    # Admin
    admin = Admin(username="admin01")
    admin.set_password("admin01login")
    db.session.add(admin)

    # Subjects
    subjects = [
        ("Data Structures", "Theory"),
        ("Database Systems", "Theory"),
        ("Operating Systems Lab", "Practical"),
        ("Networks Lab", "Practical"),
    ]
    for name, stype in subjects:
        db.session.add(Subject(name=name, subject_type=stype))

    db.session.commit()
    print("✅ Database initialized successfully with sample data!")
