import os
from app import app, db
from models import Student, Professor, Admin, Subject

DB_FILE = "gcect_it_25_29.db"

# ----------------- Step 1: Delete old database -----------------
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"🗑️  Deleted old database: {DB_FILE}")
else:
    print("No existing database found. Creating new one...")

# ----------------- Step 2: Create tables -----------------
with app.app_context():
    # Drop all tables first
    db.drop_all()
    print("🗑️  Dropped all existing tables")

    # Then recreate
    db.create_all()
    print("✅ Tables created successfully!")

    print("✅ Tables created successfully!")

    # ----------------- Step 3: Add sample Students -----------------
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

    # ----------------- Step 4: Add sample Professors -----------------
    professors = [
        ("P101", "Dr. Arindam Banerjee"),
        ("P102", "Dr. Debanjan Dey"),
    ]
    for i, (pid, name) in enumerate(professors, start=1):
        p = Professor(prof_id=pid, name=name)
        p.set_password(f"prof{str(i).zfill(2)}login")
        db.session.add(p)

    # ----------------- Step 5: Add Admin -----------------
    admin = Admin(username="admin01")
    admin.set_password("admin01login")
    db.session.add(admin)

    # ----------------- Step 6: Add Subjects -----------------
    subjects = [
        ("Data Structures", "Theory"),
        ("Database Systems", "Theory"),
        ("Operating Systems Lab", "Practical"),
        ("Networks Lab", "Practical"),
    ]
    for name, stype in subjects:
        db.session.add(Subject(name=name, subject_type=stype))

    # Commit everything
    db.session.commit()
    print("✅ Sample data inserted successfully!")

    # ----------------- Step 7: Verification -----------------
    print("\n--- Database Verification ---")
    print("Students:")
    for s in Student.query.all():
        print(f"  {s.roll} | {s.name} | Group {s.group} | CR: {s.is_cr}")

    print("\nProfessors:")
    for p in Professor.query.all():
        print(f"  {p.prof_id} | {p.name}")

    print("\nAdmin:")
    for a in Admin.query.all():
        print(f"  {a.username}")

    print("\nSubjects:")
    for sub in Subject.query.all():
        print(f"  {sub.name} ({sub.subject_type})")

    print("\n✅ Database reset and verified successfully!")
