from flask import Flask, render_template, request, redirect, sessions, url_for, session, Response
from database import (
    add_student,
    get_all_students,
    get_attendance_report,
    get_all_semesters,
    get_sections_by_semester,
    add_faculty,
    get_all_faculty,
    add_subject,
    get_subjects_with_semester,
    get_subjects,
    add_schedule,
    get_full_schedule,
    delete_schedule,
    get_schedule_by_id,
    update_schedule,
    get_dashboard_students,
    get_filtered_schedule,
    get_filtered_attendance_report,
    get_students_for_current_class,
    mark_manual_attendance,
    get_attendance_percentage_report,
    create_extra_class,
    mark_class_not_conducted,
    get_today_class_sessions,
    get_dashboard_semester_data,
    get_daily_attendance_sheet,
    get_monthly_attendance_sheet,
    get_student_attendance_report,
    system_health_check,
    get_subjects_by_semester,
    subject_exists,
    update_subject,
    get_subject_by_id,
    delete_subject,
    get_user_by_username,
    get_teacher_today_classes,
    get_students_for_teacher_current_class,
    get_teacher_dashboard_data,
    get_all_users,
    add_user,
    update_user,
    reset_user_password,
    deactivate_user,
    add_class_topics,
    create_or_get_class_session,
    get_existing_class_session,
    get_topics_by_class_session,
    get_teacher_attendance_records,
)

from face_engine import register_student_face, start_class_attendance_engine_deepface
from datetime import datetime
import threading
import csv
import io
import cv2
import numpy as np
import os
import sys
from werkzeug.utils import secure_filename
from database import get_connection


app = Flask(__name__)
app.secret_key = "szic_secret_key"
app.jinja_env.globals.update(enumerate=enumerate)

# ─── LOGIN ───────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)

        if user and user['password'] == password:

            session['logged_in'] = True
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['faculty_id'] = user['faculty_id']

            if user['role'] == 'admin':
                return redirect(url_for('dashboard'))

            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))

        else:
            error = "Wrong username or password!"

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get('logged_in'):
            return redirect(url_for('login'))

        if session.get('role') != 'admin':
            return render_template(
                'system_error.html',
                title="Access Denied",
                message="You are not authorized to access this page.",
                suggestion="Please login with an administrator account."
            )

        return f(*args, **kwargs)

    return decorated_function


# ─── DASHBOARD ───────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher_dashboard'))

    today = datetime.now().strftime("%Y-%m-%d")
    semester_data = get_dashboard_semester_data()
    print(semester_data)

    return render_template(
        'dashboard.html',
        today=today,
        semester_data=semester_data
    )


from database import (add_student, get_all_students, get_attendance_report,
                      get_subjects, get_todays_schedule, get_current_class,
                      get_students_by_subject, enroll_student,
                      mark_attendance_class, get_attendance_by_subject)

# ─── SUBJECTS LIST ───────────────────────────────────────
@app.route('/subjects', methods=['GET', 'POST'])
@admin_required
def subjects():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    selected_semester_id = request.args.get('semester_id')

    if request.method == 'POST':
        subject_name = request.form['subject_name'].strip()
        semester_id = request.form['semester_id']

        if not subject_name or not semester_id:
            return redirect(url_for('subjects'))

        if subject_exists(subject_name, semester_id):
            semesters = get_all_semesters()
            subjects_list = get_subjects()

            return render_template(
                'subjects.html',
                subjects=subjects_list,
                semesters=semesters,
                selected_semester_id=selected_semester_id,
                error="Ye subject is semester mein already exist karta hai."
            )

        add_subject(subject_name, semester_id)

        return redirect(url_for('subjects'))

    semesters = get_all_semesters()
    subjects_list = get_subjects()

    if selected_semester_id:
        subjects_list = [
            s for s in subjects_list
            if str(s.get('semester_id')) == str(selected_semester_id)
        ]

    return render_template(
        'subjects.html',
        subjects=subjects_list,
        semesters=semesters,
        selected_semester_id=selected_semester_id
    )

@app.route('/edit_subject/<int:subject_id>', methods=['POST'])
@admin_required
def edit_subject(subject_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    subject_name = request.form['subject_name'].strip()
    semester_id = request.form['semester_id']

    if not subject_name or not semester_id:
        return redirect(url_for('subjects'))

    update_subject(subject_id, subject_name, semester_id)

    return redirect(url_for('subjects'))


@app.route('/delete_subject/<int:subject_id>')
@admin_required
def delete_subject_route(subject_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    delete_subject(subject_id)

    return redirect(url_for('subjects'))

# ─── SUBJECT DETAIL (students + attendance) ──────────────
@app.route('/subject/<int:subject_id>')
@admin_required
def subject_detail(subject_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    subjects_list = get_subjects()
    subject = next((s for s in subjects_list if s['id'] == subject_id), None)
    students = get_students_by_subject(subject_id)
    all_students = get_all_students()
    attendance = get_attendance_by_subject(subject_id)

    return render_template('subject_detail.html',
                           subject=subject,
                           students=students,
                           all_students=all_students,
                           attendance=attendance)

# ─── ENROLL STUDENT IN SUBJECT ───────────────────────────
@app.route('/enroll', methods=['POST'])
@admin_required
def enroll():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    subject_id = request.form['subject_id']
    enroll_student(student_id, subject_id)

    return redirect(url_for('subject_detail', subject_id=subject_id))

@app.route('/start_class_attendance/<int:schedule_id>')
def start_class_attendance(schedule_id):

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if session.get('role') != 'teacher':
        return render_template(
            "system_error.html",
            title="Access Denied",
            message="Attendance sirf assigned teacher start kar sakta hai.",
            suggestion="Please teacher account se login karein."
        )

    faculty_id = session.get('faculty_id')

    conn = get_connection()
    # cursor = conn.cursor(dictionary=True)
    # conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM schedule
        WHERE id = ?
        AND faculty_id = ?
    """, (schedule_id, faculty_id))

    allowed_class = cursor.fetchone()

    cursor.close()
    conn.close()

    if not allowed_class:
        return render_template(
            "system_error.html",
            title="Access Denied",
            message="Ye class aapko assign nahi hai.",
            suggestion="Please sirf apni assigned class ki attendance start karein."
        )

    t = threading.Thread(
        target=start_class_attendance_engine_deepface,
        args=(schedule_id,)
    )
    t.daemon = True
    t.start()

    return redirect(url_for('teacher_dashboard'))

# ─── REGISTER PAGE ───────────────────────────────────────
@app.route('/register')
@admin_required
def register():

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    students = get_all_students()

    semesters = get_all_semesters()

    # default first semester sections
    first_semester_id = semesters[0]['id']

    sections = get_sections_by_semester(first_semester_id)

    return render_template(
        'register.html',
        students=students,
        semesters=semesters,
        sections=sections
    )


@app.route('/academic-setup', methods=['GET', 'POST'])
@admin_required
def academic_setup():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'faculty':
            name = request.form['faculty_name']
            email = request.form.get('email')
            phone = request.form.get('phone')

            add_faculty(name, email, phone)

        elif form_type == 'subject':
            subject_name = request.form['subject_name']
            semester_id = request.form['semester_id']

            add_subject(subject_name, semester_id)

        return redirect(url_for('academic_setup'))

    semesters = get_all_semesters()
    faculty = get_all_faculty()
    subjects = get_subjects_with_semester()

    return render_template(
        'academic_setup.html',
        semesters=semesters,
        faculty=faculty,
        subjects=subjects
    )

@app.route('/timetable', methods=['GET', 'POST'])
@admin_required
def timetable():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        section_id = request.form['section_id']
        subject_id = request.form['subject_id']
        faculty_id = request.form['faculty_id']
        day = request.form['day']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        add_schedule(
            section_id,
            subject_id,
            faculty_id,
            day,
            start_time,
            end_time,
        )

        return redirect(url_for('timetable'))

    semesters = get_all_semesters()
    first_semester_id = semesters[0]['id']
    sections = get_sections_by_semester(first_semester_id)

    subjects = get_subjects()
    faculty = get_all_faculty()
    schedule = get_full_schedule()

    return render_template(
        'timetable.html',
        semesters=semesters,
        sections=sections,
        subjects=subjects,
        faculty=faculty,
        schedule=schedule
    )

@app.route('/register_camera', methods=['POST'])
def register_camera():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if not system_health_check():
        return render_template(
            "system_error.html",
            title="System Not Ready",
            message="Camera registration start nahi ho sakti kyun ke database connection available nahi hai.",
            suggestion="Please XAMPP/MySQL start karein, phir software refresh karke registration dobara try karein."
        )

    name = request.form['name']
    roll_no = request.form['roll_no']
    gender = request.form.get('gender', 'Male')
    section_id = request.form['section_id']

    if gender == "Female":
        return render_template(
            "system_error.html",
            title="Photo Registration Disabled",
            message="Female students ke liye camera/photo registration allowed nahi hai.",
            suggestion="Please Register Female Student Without Photo option use karein."
        )

    photo_path = register_student_face(name, roll_no)

    if not photo_path:
        return render_template(
            "system_error.html",
            title="Camera Registration Failed",
            message="Student face samples properly save nahi ho sake.",
            suggestion="Camera connection check karein aur good lighting me dobara try karein."
        )

    add_student(name, roll_no, section_id, photo_path, gender)

    return redirect(url_for('register'))


# ─── REGISTER VIA IMAGE UPLOAD ───────────────────────────
@app.route('/register_upload', methods=['POST'])
@admin_required
def register_upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if not system_health_check():
        return render_template(
            "system_error.html",
            title="System Not Ready",
            message="Student registration start nahi ho sakti kyun ke database connection available nahi hai.",
            suggestion="Please XAMPP/MySQL start karein, phir software refresh karke registration dobara try karein."
        )

    name = request.form['name'].strip()
    roll_no = request.form['roll_no'].strip()
    gender = request.form.get('gender', 'Male')
    section_id = request.form['section_id']
    photo = request.files['photo']

    if gender == "Female":
        return render_template(
            "system_error.html",
            title="Photo Upload Disabled",
            message="Female students ke liye face/photo registration allowed nahi hai.",
            suggestion="Please Register Female Student Without Photo option use karein."
        )

    if photo.filename == '':
        return redirect(url_for('register'))

    student_folder = f"student_images/{roll_no}"
    os.makedirs(student_folder, exist_ok=True)

    existing_images = [
        f for f in os.listdir(student_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    next_no = len(existing_images) + 1
    ext = os.path.splitext(photo.filename)[1].lower()

    if ext not in [".jpg", ".jpeg", ".png"]:
        ext = ".jpg"

    photo_path = f"{student_folder}/{next_no}{ext}"
    photo.save(photo_path)

    # Agar roll number pehle se database mein nahi hai tab add karo
    students = get_all_students()
    already_exists = any(str(s["roll_no"]) == str(roll_no) for s in students)

    if not already_exists:
        add_student(name, roll_no, section_id, photo_path, gender)

    semesters = get_all_semesters()
    sections = get_sections_by_semester(semesters[0]['id'])

    return render_template(
        'register.html',
        message=f"'{name}' image upload se register/update ho gaya. Total images: {next_no} ✅",
        students=get_all_students(),
        semesters=semesters,
        sections=sections
    )


@app.route('/register_manual', methods=['POST'])
@admin_required
def register_manual():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.form['name']
    roll_no = request.form['roll_no']
    section_id = request.form['section_id']
    gender = request.form.get('gender', 'Female')

    try:
        photo_path = None

        add_student(
            name,
            roll_no,
            section_id,
            photo_path,
            gender
        )

        return redirect(url_for('register'))

    except Exception as e:
        print("[ERROR] Manual registration failed:", e)
        return redirect(url_for('register'))

# ─── START ATTENDANCE ────────────────────────────────────
@app.route('/start_attendance')
def start():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    t = threading.Thread(target=start_attendance)
    t.daemon = True
    t.start()

    return redirect(url_for('dashboard'))

# ─── REPORTS ─────────────────────────────────────────────
@app.route('/reports')
@admin_required
def reports():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    report_type = request.args.get('report_type', 'daily')

    date_filter = request.args.get('date')
    month_filter = request.args.get('month')
    section_id = request.args.get('section_id')
    subject_id = request.args.get('subject_id')
    search_text = request.args.get('search_text')

    section_id_int = int(section_id) if section_id else None
    subject_id_int = int(subject_id) if subject_id else None

    daily_sheet = []
    monthly_sheet = []

    monthly_summary = {
    "total_students": 0,
    "conducted_classes": 0,
    "average_attendance": 0
    }

    monthly_sessions = []
    student_info = None
    student_records = []
    detailed_records = []

    if report_type == 'daily' and date_filter and section_id_int and subject_id_int:
        daily_sheet = get_daily_attendance_sheet(
            date_filter,
            section_id_int,
            subject_id_int
        )

    elif report_type == 'monthly' and month_filter and section_id_int and subject_id_int:
        year, month = month_filter.split('-')

        monthly_sessions, monthly_sheet = get_monthly_attendance_sheet(
            int(year),
            int(month),
            section_id_int,
            subject_id_int
        )

        total_students = len(monthly_sheet)
        conducted_classes = len(monthly_sessions)

        if total_students > 0:
            total_percentage = sum(row["percentage"] for row in monthly_sheet)
            average_attendance = round(total_percentage / total_students, 1)
        else:
            average_attendance = 0

        monthly_summary = {
            "total_students": total_students,
            "conducted_classes": conducted_classes,
            "average_attendance": average_attendance
        }

    elif report_type == 'student' and search_text:
        student_info, student_records = get_student_attendance_report(search_text)

    elif report_type == 'records':
        detailed_records = get_filtered_attendance_report(
            date=date_filter,
            section_id=section_id_int,
            subject_id=subject_id_int
        )

    semesters = get_all_semesters()

    all_sections = []
    for sem in semesters:
        sections = get_sections_by_semester(sem['id'])
        for sec in sections:
            all_sections.append({
                "id": sec["id"],
                "section_name": sec["name"],
                "semester_no": sem["semester_no"],
                "session_name": sem["session_name"]
            })

    subjects = get_subjects()

    return render_template(
        'reports.html',
        report_type=report_type,
        date_filter=date_filter,
        month_filter=month_filter,
        selected_section_id=section_id_int,
        selected_subject_id=subject_id_int,
        search_text=search_text,
        all_sections=all_sections,
        subjects=subjects,
        daily_sheet=daily_sheet,
        monthly_sheet=monthly_sheet,
        monthly_sessions=monthly_sessions,
        monthly_summary=monthly_summary,
        student_info=student_info,
        student_records=student_records,
        detailed_records=detailed_records    
    )
    
# ─── EXPORT CSV (pandas ki jagah) ────────────────────────
@app.route('/export')
@admin_required
def export():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    report = get_filtered_attendance_report()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Student Name',
        'Roll No',
        'Subject',
        'Semester',
        'Section',
        'Date',
        'Time',
        'Status'
    ])

    for row in report:
        writer.writerow([
            row['name'],
            row['roll_no'],
            row['subject_name'],
            row['semester_no'],
            row['section_name'],
            row['date'],
            row['time'],
            row['status']
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment;filename=attendance_report.csv"
        }
    )
# ─── DELETE STUDENT ──────────────────────────────────────
# @app.route('/delete_student/<int:student_id>')
# @admin_required
# def delete_student(student_id):
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))

#     conn = get_connection()
#     cursor = conn.cursor()

#     # Pehle linked data delete karo
#     cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))

#     # Student ka roll_no lo images delete karne ke liye
#     cursor.execute("SELECT roll_no FROM students WHERE id=?", (student_id,))
#     student = cursor.fetchone()

#     # Student delete karo
#     cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
#     conn.commit()
#     cursor.close()
#     conn.close()

#     # Images folder delete karo
#     if student:
#         import shutil
#         folder = f"student_images/{student[0]}"
#         if os.path.exists(folder):
#             shutil.rmtree(folder)

#     # Model retrain karo
#     # train_model()

#     return redirect(url_for('register'))

# ─── DELETE STUDENT ──────────────────────────────────────
@app.route('/delete_student/<int:student_id>')
@admin_required
def delete_student(student_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_connection()
    
    # SQLite row_factory set karein taake field names dictionary ki tarah access hon
    # conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    cursor = conn.cursor()

    try:
        # Pehle linked data delete karo
        cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))

        # Student ka roll_no lo images delete karne ke liye
        cursor.execute("SELECT roll_no FROM students WHERE id=?", (student_id,))
        student = cursor.fetchone()

        # Student delete karo
        cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
        conn.commit()
    
    except Exception as e:
        print("[DATABASE ERROR In Delete]:", e)
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

    # Images folder delete karo (Bug Fix)
    if student:
        # Agar dictionary hai to 'roll_no' se nikalein, warna tuple hai to index 0 se
        roll_no = student.get('roll_no') if isinstance(student, dict) else student[0]
        
        if roll_no:
            import shutil
            folder = f"student_images/{roll_no}"
            if os.path.exists(folder):
                shutil.rmtree(folder)

    # Model retrain karo
    # train_model()

    return redirect(url_for('register'))

@app.route('/get_sections/<int:semester_id>')
@admin_required
def get_sections_api(semester_id):
    if not session.get('logged_in'):
        return {"error": "Unauthorized"}, 401

    sections = get_sections_by_semester(semester_id)
    return {"sections": sections}

@app.route('/delete_schedule/<int:schedule_id>')
@admin_required
def delete_schedule_route(schedule_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    delete_schedule(schedule_id)
    return redirect(url_for('timetable'))


@app.route('/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
@admin_required
def edit_schedule(schedule_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        section_id = request.form['section_id']
        subject_id = request.form['subject_id']
        faculty_id = request.form['faculty_id']
        day = request.form['day']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        update_schedule(schedule_id, section_id, subject_id, faculty_id, day, start_time, end_time)
        return redirect(url_for('timetable'))

    edit_item = get_schedule_by_id(schedule_id)

    semesters = get_all_semesters()
    sections = get_sections_by_semester(semesters[0]['id'])
    subjects = get_subjects()
    faculty = get_all_faculty()
    schedule = get_full_schedule()

    return render_template(
        'timetable.html',
        semesters=semesters,
        sections=sections,
        subjects=subjects,
        faculty=faculty,
        schedule=schedule,
        edit_item=edit_item
    )

@app.route('/start_current_class_attendance')
def start_current_class_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_class = get_current_class()

    if not current_class:
        return redirect(url_for('dashboard'))

    from face_engine import start_class_attendance_engine

    t = threading.Thread(
        target=start_class_attendance_engine,
        args=(current_class['schedule_id'],)
    )
    t.daemon = True
    t.start()

    return redirect(url_for('dashboard'))


@app.route('/manual-attendance', methods=['GET', 'POST'])
def manual_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if session.get('role') == 'admin':
        return render_template(
            "system_error.html",
            title="Access Denied",
            message="Manual attendance sirf teacher account se mark ho sakti hai.",
            suggestion="Please teacher login se apni assigned class ki attendance mark karein."
        )

    # Teacher ke liye sirf apni current class
    if session.get('role') == 'teacher':
        faculty_id = session.get('faculty_id')
        current_class, students = get_students_for_teacher_current_class(faculty_id)

    # Admin ke liye normal current class
    else:
        current_class, students = get_students_for_current_class()

    if request.method == 'POST':

        if not current_class:
            return redirect(url_for('manual_attendance'))

        # Extra safety: teacher sirf apni class mark kare
        if session.get('role') == 'teacher':
            if not current_class:
                return render_template(
                    "system_error.html",
                    title="No Active Class",
                    message="Aapki is waqt koi active class nahi hai.",
                    suggestion="Please apni scheduled class timing par attendance mark karein."
                )

        for student in students:
            status = request.form.get(f"status_{student['id']}", "Absent")

            mark_manual_attendance(
                student_id=student["id"],
                schedule_id=current_class["schedule_id"],
                subject_id=current_class["subject_id"],
                section_id=current_class["section_id"],
                status=status
            )

        if session.get('role') == 'teacher':
            return redirect(url_for('teacher_dashboard'))

        return redirect(url_for('reports'))

    return render_template(
        'manual_attendance.html',
        current_class=current_class,
        students=students
    )

@app.route('/analytics')
@admin_required
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    section_id = request.args.get('section_id', None)
    subject_id = request.args.get('subject_id', None)

    section_id = int(section_id) if section_id else None
    subject_id = int(subject_id) if subject_id else None

    data = get_attendance_percentage_report(
        section_id=section_id,
        subject_id=subject_id
    )

    semesters = get_all_semesters()

    all_sections = []
    for sem in semesters:
        sections = get_sections_by_semester(sem['id'])
        for sec in sections:
            all_sections.append({
                "id": sec["id"],
                "section_name": sec["name"],
                "semester_no": sem["semester_no"],
                "session_name": sem["session_name"]
            })

    subjects = get_subjects()

    return render_template(
        'analytics.html',
        data=data,
        all_sections=all_sections,
        subjects=subjects,
        selected_section_id=section_id,
        selected_subject_id=subject_id
    )

@app.route('/class-sessions', methods=['GET', 'POST'])
def class_sessions():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':

        action = request.form.get('action')

        # =========================
        # NOT CONDUCTED
        # =========================

        if action == 'not_conducted':

            session_id = request.form.get('session_id')
            remarks = request.form.get('remarks')

            mark_class_not_conducted(
                session_id,
                remarks
            )

        # =========================
        # EXTRA CLASS
        # =========================

        elif action == 'extra_class':

            section_id = request.form.get('section_id')
            subject_id = request.form.get('subject_id')
            faculty_id = request.form.get('faculty_id')

            session_date = request.form.get('session_date')

            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            remarks = request.form.get('remarks')

            create_extra_class(
                section_id,
                subject_id,
                faculty_id,
                session_date,
                start_time,
                end_time,
                remarks
            )

        return redirect(url_for('class_sessions'))

    sessions = get_today_class_sessions()

    total_sessions = len(sessions)
    conducted_sessions = sum(1 for s in sessions if s["status"] == "Conducted")
    not_conducted_sessions = sum(1 for s in sessions if s["status"] != "Conducted")
    extra_sessions = sum(1 for s in sessions if s["session_type"] == "Extra")
    semesters = get_all_semesters()

    all_sections = []

    for sem in semesters:
        sections = get_sections_by_semester(sem['id'])

        for sec in sections:
            all_sections.append({
                "id": sec["id"],
                "section_name": sec["name"],
                "semester_no": sem["semester_no"]
            })

    subjects = get_subjects()
    faculty = get_all_faculty()

    return render_template(
        'class_sessions.html',
        sessions=sessions,
        all_sections=all_sections,
        subjects=subjects,
        faculty=faculty,
        total_sessions=total_sessions,
        conducted_sessions=conducted_sessions,
        not_conducted_sessions=not_conducted_sessions,
        extra_sessions=extra_sessions
    )

@app.route('/get_subjects/<int:semester_id>')
@admin_required
def get_subjects_api(semester_id):
    if not session.get('logged_in'):
        return {"error": "Unauthorized"}, 401

    subjects = get_subjects_by_semester(semester_id)
    return {"subjects": subjects}

def get_today_day_code():
    days = {
        "Monday": "MON",
        "Tuesday": "TUE",
        "Wednesday": "WED",
        "Thursday": "THU",
        "Friday": "FRI",
        "Saturday": "SAT",
        "Sunday": "SUN"
    }

    today_name = datetime.now().strftime("%A")
    return days.get(today_name)

@app.route('/teacher-dashboard')
def teacher_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if session.get('role') != 'teacher':
        return redirect(url_for('dashboard'))

    faculty_id = session.get('faculty_id')
    today_day = get_today_day_code()

    active_class, today_schedule = get_teacher_dashboard_data(
        faculty_id,
        today_day
    )

    return render_template(
        'teacher_dashboard.html',
        active_class=active_class,
        today_schedule=today_schedule,
        today_day=today_day
    )

# @app.route('/teacher/start-attendance/<int:schedule_id>')
# def teacher_start_attendance(schedule_id):

#     if not session.get('logged_in'):
#         return redirect(url_for('login'))

#     if session.get('role') != 'teacher':
#         return redirect(url_for('dashboard'))

#     faculty_id = session.get('faculty_id')

#     conn = get_connection()
#     conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT *
#         FROM schedule
#         WHERE id = ?
#         AND faculty_id = ?
#     """, (schedule_id, faculty_id))

#     schedule = cursor.fetchone()

#     cursor.close()
#     conn.close()

#     if not schedule:
#         return render_template(
#             "system_error.html",
#             title="Access Denied",
#             message="Ye class aapko assign nahi hai.",
#             suggestion="Please apni assigned classes hi access karein."
#         )

#     return redirect(
#         url_for(
#             'start_class_attendance',
#             schedule_id=schedule_id
#         )
#     )

@app.route('/teacher/start-attendance/<int:schedule_id>')
def teacher_start_attendance(schedule_id):

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if session.get('role') != 'teacher':
        return redirect(url_for('dashboard'))

    faculty_id = session.get('faculty_id')

    conn = get_connection()
    # SQLite row_factory lagayein taake dictionary format me data mile
    # conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM schedule
        WHERE id = ?
        AND faculty_id = ?
    """, (schedule_id, faculty_id))

    schedule = cursor.fetchone()

    cursor.close()
    conn.close()

    if not schedule:
        return render_template(
            "system_error.html",
            title="Access Denied",
            message="Ye class aapko assign nahi hai.",
            suggestion="Please apni assigned classes hi access karein."
        )

    return redirect(
        url_for(
            'start_class_attendance',
            schedule_id=schedule_id
        )
    )
    
@app.route('/teacher/attendance-records')
def teacher_attendance_records():

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if session.get('role') != 'teacher':
        return redirect(url_for('dashboard'))

    faculty_id = session.get('faculty_id')

    records = get_teacher_attendance_records(faculty_id)

    return render_template(
        'teacher_attendance_records.html',
        records=records
    )

@app.route('/users', methods=['GET', 'POST'])
@admin_required
def users():

    if request.method == 'POST':

        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        faculty_id = request.form['faculty_id']

        add_user(
            name=name,
            username=username,
            password=password,
            role='teacher',
            faculty_id=faculty_id
        )

        return redirect(url_for('users'))

    users_list = get_all_users()
    faculty_list = get_all_faculty()

    return render_template(
        'users.html',
        users=users_list,
        faculty=faculty_list
    )

@app.route('/reset_user_password/<int:user_id>', methods=['POST'])
@admin_required
def reset_user_password_route(user_id):

    new_password = request.form['new_password']

    reset_user_password(user_id, new_password)

    return redirect(url_for('users'))


@app.route('/toggle_user_status/<int:user_id>/<int:status>')
@admin_required
def toggle_user_status(user_id, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_active = ?
        WHERE id = ?
    """, (status, user_id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('users'))

@app.route('/attendance_topics/<int:schedule_id>', methods=['GET', 'POST'])
def attendance_topics(schedule_id):

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    existing_session = get_existing_class_session(schedule_id)

    if existing_session:
        existing_topics = get_topics_by_class_session(existing_session["id"])

        if existing_topics:
            return redirect(
                url_for(
                    'start_class_attendance',
                    schedule_id=schedule_id
                )
            )

    if request.method == 'POST':

        class_session_id = request.form['class_session_id']
        topics = request.form.getlist('topics')

        add_class_topics(class_session_id, topics)

        return redirect(
            url_for(
                'start_class_attendance',
                schedule_id=schedule_id
            )
        )

    current_class = get_schedule_by_id(schedule_id)

    class_session_id = create_or_get_class_session(schedule_id)

    return render_template(
        'attendance_topics.html',
        current_class=current_class,
        class_session_id=class_session_id
    )

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)

