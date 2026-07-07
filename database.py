import sqlite3
from datetime import datetime
import os
import sys

# def get_connection():
#     # Flask application mein multi-threading issues se bachne ke liye check_same_thread=False zaroori hai
#     conn = sqlite3.connect("database.db", check_same_thread=False)
#     # Is row_factory se SQLite ke results dict (dictionary) format mein milte hain, jaisa MySQL mein tha
#     conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
#     return conn
import os
import sqlite3

# def get_connection():
#     # Yeh aapki current database.py file ka folder dhoondega (D:\Projects\Khayyam_dlib\Khayyam_dlib)
#     base_path = os.path.dirname(os.path.abspath(__file__))
#     db_path = os.path.join(base_path, 'database.db')
    
#     # Absolute path par connect karein
#     conn = sqlite3.connect(db_path, check_same_thread=False)
#     conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
#     return conn

def get_connection():
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'database.db')

    print("\n====================")
    print("DATABASE:", db_path)
    print("====================\n")

    conn = sqlite3.connect(
        db_path,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = lambda cursor, row: {
        col[0]: row[idx]
        for idx, col in enumerate(cursor.description)
    }

    return conn

# ================================
# SESSIONS / SEMESTERS / SECTIONS
# ================================

def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions ORDER BY id")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_all_semesters():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            semesters.id,
            semesters.semester_no,
            sessions.name AS session_name
        FROM semesters
        JOIN sessions ON semesters.session_id = sessions.id
        ORDER BY semesters.semester_no
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_sections_by_semester(semester_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM sections
        WHERE semester_id = ?
        ORDER BY name
    """, (semester_id,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# ================================
# STUDENT MANAGEMENT
# ================================

def add_student(name, roll_no, section_id, photo_path, gender):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO students
        (name, roll_no, section_id, photo_path, gender)
        VALUES (?, ?, ?, ?, ?)
    """, (name, roll_no, section_id, photo_path, gender))

    conn.commit()

    cursor.close()
    conn.close()

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.roll_no,
            students.photo_path,
            sections.id AS section_id,
            sections.name AS section_name,
            semesters.id AS semester_id,
            semesters.semester_no
        FROM students
        JOIN sections ON students.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        ORDER BY semesters.semester_no, sections.name, students.roll_no
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_student_by_id(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE id = ?
    """, (student_id,))

    data = cursor.fetchone()

    cursor.close()
    conn.close()
    return data


# ================================
# FACULTY MANAGEMENT
# ================================

def add_faculty(name, email=None, phone=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO faculty (name, email, phone)
        VALUES (?, ?, ?)
    """, (name, email, phone))

    conn.commit()

    cursor.close()
    conn.close()


def get_all_faculty():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM faculty
        ORDER BY name
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# ================================
# SUBJECT MANAGEMENT
# ================================

def add_subject(name, semester_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO subjects (name, semester_id)
        VALUES (?, ?)
    """, (name, semester_id))

    conn.commit()

    cursor.close()
    conn.close()


def get_subjects():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            subjects.id,
            subjects.name,
            subjects.semester_id,
            semesters.semester_no
        FROM subjects
        JOIN semesters ON subjects.semester_id = semesters.id
        ORDER BY semesters.semester_no, subjects.name
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_subjects_with_semester():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            subjects.id,
            subjects.name,
            semesters.semester_no,
            sessions.name AS session_name
        FROM subjects
        JOIN semesters ON subjects.semester_id = semesters.id
        JOIN sessions ON semesters.session_id = sessions.id
        ORDER BY semesters.semester_no, subjects.name
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# ================================
# TIMETABLE / SCHEDULE
# ================================

def get_todays_schedule():
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    today = days[datetime.now().weekday()]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            schedule.id,
            schedule.day,
            schedule.start_time,
            schedule.end_time,
            subjects.id AS subject_id,
            subjects.name AS subject_name,
            faculty.id AS faculty_id,
            faculty.name AS teacher,
            semesters.semester_no,
            sections.id AS section_id,
            sections.name AS section_name
        FROM schedule
        JOIN subjects ON schedule.subject_id = subjects.id
        JOIN faculty ON schedule.faculty_id = faculty.id
        JOIN sections ON schedule.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        WHERE schedule.day = ?
        ORDER BY schedule.start_time
    """, (today,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_current_class():
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    today = days[datetime.now().weekday()]
    now_time = datetime.now().strftime("%H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            schedule.id AS schedule_id,
            schedule.start_time,
            schedule.end_time,
            subjects.id AS subject_id,
            subjects.name AS subject_name,
            faculty.name AS teacher,
            semesters.semester_no,
            sections.id AS section_id,
            sections.name AS section_name
        FROM schedule
        JOIN subjects ON schedule.subject_id = subjects.id
        JOIN faculty ON schedule.faculty_id = faculty.id
        JOIN sections ON schedule.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        WHERE schedule.day = ?
        AND ? BETWEEN schedule.start_time AND schedule.end_time
        LIMIT 1
    """, (today, now_time))

    data = cursor.fetchone()

    cursor.close()
    conn.close()
    return data


def add_schedule(section_id, subject_id, faculty_id, day, start_time, end_time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO schedule
        (section_id, subject_id, faculty_id, day, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        section_id,
        subject_id,
        faculty_id,
        day,
        start_time,
        end_time
    ))

    conn.commit()

    cursor.close()
    conn.close()

def get_full_schedule():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            schedule.id,
            schedule.day,
            schedule.start_time,
            schedule.end_time,
            subjects.name AS subject_name,
            faculty.name AS teacher,
            semesters.semester_no,
            sections.name AS section_name
        FROM schedule
        JOIN subjects ON schedule.subject_id = subjects.id
        JOIN faculty ON schedule.faculty_id = faculty.id
        JOIN sections ON schedule.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        ORDER BY semesters.semester_no, sections.name, schedule.day, schedule.start_time
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# ================================
# ATTENDANCE MANAGEMENT
# ================================

def mark_attendance(student_id, status="Present"):
    current_class = get_current_class()

    if not current_class:
        return False

    now = datetime.now()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT section_id
        FROM students
        WHERE id = ?
    """, (student_id,))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return False

    if student["section_id"] != current_class["section_id"]:
        cursor.close()
        conn.close()
        return False

    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE student_id = ?
        AND schedule_id = ?
        AND date = ?
    """, (
        student_id,
        current_class["schedule_id"],
        now.strftime("%Y-%m-%d")
    ))

    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO attendance
            (student_id, schedule_id, subject_id, section_id, date, time, status, marked_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            current_class["schedule_id"],
            current_class["subject_id"],
            current_class["section_id"],
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            status,
            "Face Recognition"
        ))

        conn.commit()

    cursor.close()
    conn.close()
    return True


def mark_attendance_class(student_id, subject_id, schedule_id, class_session_id=None, status="Present"):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT section_id
        FROM schedule
        WHERE id = ?
    """, (schedule_id,))

    schedule_data = cursor.fetchone()

    if not schedule_data:
        cursor.close()
        conn.close()
        return False

    section_id = schedule_data["section_id"]

    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE student_id = ?
        AND schedule_id = ?
        AND date = ?
    """, (student_id, schedule_id, today))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE attendance
            SET class_session_id = ?,
                subject_id = ?,
                section_id = ?,
                time = ?,
                status = ?,
                marked_by = ?
            WHERE id = ?
        """, (
            class_session_id,
            subject_id,
            section_id,
            current_time,
            status,
            "DeepFace Recognition",
            existing["id"]
        ))

        conn.commit()

        cursor.close()
        conn.close()

        print(f"[INFO] Attendance already existed. Updated record ID: {existing['id']}")
        return True

    cursor.execute("""
        INSERT INTO attendance
        (student_id, schedule_id, class_session_id, subject_id, section_id, date, time, status, marked_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        schedule_id,
        class_session_id,
        subject_id,
        section_id,
        today,
        current_time,
        status,
        "DeepFace Recognition"
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return True

def get_attendance_report(date=None):
    conn = get_connection()
    cursor = conn.cursor()

    if date:
        cursor.execute("""
            SELECT
                students.name,
                students.roll_no,
                attendance.date,
                attendance.time,
                attendance.status,
                subjects.name AS subject_name,
                semesters.semester_no,
                sections.name AS section_name
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            JOIN subjects ON attendance.subject_id = subjects.id
            JOIN sections ON attendance.section_id = sections.id
            JOIN semesters ON sections.semester_id = semesters.id
            WHERE attendance.date = ?
            ORDER BY attendance.time DESC
        """, (date,))
    else:
        cursor.execute("""
            SELECT
                students.name,
                students.roll_no,
                attendance.date,
                attendance.time,
                attendance.status,
                subjects.name AS subject_name,
                semesters.semester_no,
                sections.name AS section_name
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            JOIN subjects ON attendance.subject_id = subjects.id
            JOIN sections ON attendance.section_id = sections.id
            JOIN semesters ON sections.semester_id = semesters.id
            ORDER BY attendance.date DESC, attendance.time DESC
        """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def get_attendance_by_subject(subject_id, date=None):
    conn = get_connection()
    cursor = conn.cursor()

    if date:
        cursor.execute("""
            SELECT
                students.name,
                students.roll_no,
                attendance.date,
                attendance.time,
                attendance.status,
                subjects.name AS subject_name
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            JOIN subjects ON attendance.subject_id = subjects.id
            WHERE attendance.subject_id = ?
            AND attendance.date = ?
            ORDER BY attendance.time
        """, (subject_id, date))
    else:
        cursor.execute("""
            SELECT
                students.name,
                students.roll_no,
                attendance.date,
                attendance.time,
                attendance.status,
                subjects.name AS subject_name
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            JOIN subjects ON attendance.subject_id = subjects.id
            WHERE attendance.subject_id = ?
            ORDER BY attendance.date DESC, attendance.time
        """, (subject_id,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


# ================================
# OLD SUBJECT PAGE COMPATIBILITY
# ================================

def get_students_by_subject(subject_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.roll_no,
            sections.name AS section_name,
            semesters.semester_no
        FROM students
        JOIN sections ON students.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        JOIN subjects ON subjects.semester_id = semesters.id
        WHERE subjects.id = ?
        ORDER BY students.roll_no
    """, (subject_id,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def enroll_student(student_id, subject_id):
    return True

def delete_schedule(schedule_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE schedule_id = ?", (schedule_id,))
    cursor.execute("DELETE FROM schedule WHERE id = ?", (schedule_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_schedule_by_id(schedule_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM schedule
        WHERE id = ?
    """, (schedule_id,))

    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return data


def update_schedule(schedule_id, section_id, subject_id, faculty_id, day, start_time, end_time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE schedule
        SET section_id = ?,
            subject_id = ?,
            faculty_id = ?,
            day = ?,
            start_time = ?,
            end_time = ?
        WHERE id = ?
    """, (section_id, subject_id, faculty_id, day, start_time, end_time, schedule_id))

    conn.commit()
    cursor.close()
    conn.close()

def get_students_by_section(section_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE section_id = ?
    """, (section_id,))

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return students

def get_dashboard_students(section_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if section_id:
        cursor.execute("""
            SELECT *
            FROM students
            WHERE section_id = ?
        """, (section_id,))
    else:
        cursor.execute("""
            SELECT *
            FROM students
        """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def get_filtered_schedule(section_id=None):
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    today = days[datetime.now().weekday()]

    conn = get_connection()
    cursor = conn.cursor()

    if section_id:
        cursor.execute("""
            SELECT
                schedule.id,
                schedule.day,
                schedule.start_time,
                schedule.end_time,
                subjects.name AS subject_name,
                faculty.name AS teacher,
                semesters.semester_no,
                sections.name AS section_name
            FROM schedule
            JOIN subjects ON schedule.subject_id = subjects.id
            JOIN faculty ON schedule.faculty_id = faculty.id
            JOIN sections ON schedule.section_id = sections.id
            JOIN semesters ON sections.semester_id = semesters.id
            WHERE schedule.day = ?
            AND schedule.section_id = ?
            ORDER BY schedule.start_time
        """, (today, section_id))

    else:
        cursor.execute("""
            SELECT
                schedule.id,
                schedule.day,
                schedule.start_time,
                schedule.end_time,
                subjects.name AS subject_name,
                faculty.name AS teacher,
                semesters.semester_no,
                sections.name AS section_name
            FROM schedule
            JOIN subjects ON schedule.subject_id = subjects.id
            JOIN faculty ON schedule.faculty_id = faculty.id
            JOIN sections ON schedule.section_id = sections.id
            JOIN semesters ON sections.semester_id = semesters.id
            WHERE schedule.day = ?
            ORDER BY schedule.start_time
        """, (today,))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data

def get_filtered_attendance_report(date=None, section_id=None, subject_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            students.name,
            students.roll_no,
            attendance.date,
            attendance.time,
            attendance.status,
            subjects.id AS subject_id,
            subjects.name AS subject_name,
            semesters.semester_no,
            sections.id AS section_id,
            sections.name AS section_name
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        JOIN subjects ON attendance.subject_id = subjects.id
        JOIN sections ON attendance.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        WHERE 1=1
    """

    params = []

    if date:
        query += " AND attendance.date = ?"
        params.append(date)

    if section_id:
        query += " AND attendance.section_id = ?"
        params.append(section_id)

    if subject_id:
        query += " AND attendance.subject_id = ?"
        params.append(subject_id)

    query += " ORDER BY attendance.date DESC, attendance.time DESC"

    cursor.execute(query, tuple(params))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data

def get_students_for_current_class():
    current_class = get_current_class()

    if not current_class:
        return None, []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            roll_no
        FROM students
        WHERE section_id = ?
        ORDER BY roll_no
    """, (current_class["section_id"],))

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return current_class, students


def mark_manual_attendance(student_id, schedule_id, subject_id, section_id, status):
    now = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            faculty_id,
            start_time,
            end_time
        FROM schedule
        WHERE id = ?
    """, (schedule_id,))

    schedule_data = cursor.fetchone()

    if not schedule_data:
        cursor.close()
        conn.close()
        return False

    cursor.close()
    conn.close()

    class_session_id = create_class_session(
        schedule_id=schedule_id,
        section_id=section_id,
        subject_id=subject_id,
        scheduled_faculty_id=schedule_data["faculty_id"],
        actual_faculty_id=schedule_data["faculty_id"],
        session_date=now.strftime("%Y-%m-%d"),
        start_time=schedule_data["start_time"],
        end_time=schedule_data["end_time"],
        session_type="Scheduled",
        status="Conducted",
        remarks="Manual attendance override"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE student_id = ?
        AND class_session_id = ?
        AND date = ?
    """, (
        student_id,
        class_session_id,
        now.strftime("%Y-%m-%d")
    ))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE attendance
            SET status = ?,
                time = ?,
                marked_by = 'Manual Override'
            WHERE id = ?
        """, (
            status,
            now.strftime("%H:%M:%S"),
            existing["id"]
        ))
    else:
        cursor.execute("""
            INSERT INTO attendance
            (
                student_id,
                schedule_id,
                class_session_id,
                subject_id,
                section_id,
                date,
                time,
                status,
                marked_by
            )
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            student_id,
            schedule_id,
            class_session_id,
            subject_id,
            section_id,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            status,
            "Manual Override"
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return True

def get_attendance_percentage_report(section_id=None, subject_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            students.id AS student_id,
            students.name,
            students.roll_no,

            subjects.id AS subject_id,
            subjects.name AS subject_name,

            semesters.semester_no,
            sections.name AS section_name,

            COUNT(DISTINCT class_sessions.id) AS total_conducted_classes,

            SUM(
                CASE
                    WHEN attendance.status IN ('Present', 'Late')
                    THEN 1
                    ELSE 0
                END
            ) AS present_classes

        FROM students

        JOIN sections
            ON students.section_id = sections.id

        JOIN semesters
            ON sections.semester_id = semesters.id

        LEFT JOIN attendance
            ON students.id = attendance.student_id

        LEFT JOIN class_sessions
            ON attendance.class_session_id = class_sessions.id

        LEFT JOIN subjects
            ON class_sessions.subject_id = subjects.id

        WHERE
            class_sessions.status = 'Conducted'
    """

    params = []

    if section_id:
        query += " AND class_sessions.section_id = ?"
        params.append(section_id)

    if subject_id:
        query += " AND class_sessions.subject_id = ?"
        params.append(subject_id)

    query += """
        GROUP BY
            students.id,
            students.name,
            students.roll_no,
            subjects.id,
            subjects.name,
            semesters.semester_no,
            sections.name

        ORDER BY
            semesters.semester_no,
            sections.name,
            students.roll_no
    """

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    final_rows = []

    for row in rows:
        total = row["total_conducted_classes"] or 0
        present = row["present_classes"] or 0

        if total > 0:
            percentage = round((present / total) * 100, 2)
        else:
            percentage = 0

        row["attendance_percentage"] = percentage
        row["attendance_status"] = "Safe" if percentage >= 75 else "Below 75%"
        final_rows.append(row)

    cursor.close()
    conn.close()

    return final_rows

def create_class_session(
    schedule_id, section_id, subject_id, scheduled_faculty_id,
    actual_faculty_id, session_date, start_time, end_time,
    session_type='Scheduled', status='Conducted', remarks=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM class_sessions
        WHERE section_id = ?
        AND subject_id = ?
        AND session_date = ?
        AND start_time = ?
    """, (section_id, subject_id, session_date, start_time))

    existing = cursor.fetchone()

    if existing:
        session_id = existing["id"]
    else:
        cursor.execute("""
            INSERT INTO class_sessions (
                schedule_id, section_id, subject_id, scheduled_faculty_id,
                actual_faculty_id, session_date, start_time, end_time,
                session_type, status, remarks
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            schedule_id, section_id, subject_id, scheduled_faculty_id,
            actual_faculty_id, session_date, start_time, end_time,
            session_type, status, remarks
        ))

        conn.commit()
        session_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return session_id

def get_today_class_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    # SQLite mein CURDATE() nahi hota, date('now', 'localtime') use hota hai
    cursor.execute("""
        SELECT
            class_sessions.id,
            class_sessions.session_date,
            class_sessions.start_time,
            class_sessions.end_time,
            class_sessions.session_type,
            class_sessions.status,
            class_sessions.remarks,
            class_sessions.section_id,
            class_sessions.subject_id,

            subjects.name AS subject_name,

            semesters.semester_no,
            sections.name AS section_name,

            f1.name AS scheduled_teacher,
            f2.name AS actual_teacher,

            (
                SELECT COUNT(*)
                FROM students
                WHERE students.section_id = class_sessions.section_id
            ) AS total_students,

            (
                SELECT COUNT(DISTINCT attendance.student_id)
                FROM attendance
                WHERE attendance.class_session_id = class_sessions.id
                AND attendance.status IN ('Present', 'Late', 'Late Present')
            ) AS present_count

        FROM class_sessions

        JOIN subjects ON class_sessions.subject_id = subjects.id
        JOIN sections ON class_sessions.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        LEFT JOIN faculty f1 ON class_sessions.scheduled_faculty_id = f1.id
        LEFT JOIN faculty f2 ON class_sessions.actual_faculty_id = f2.id
        WHERE class_sessions.session_date = date('now', 'localtime')
        ORDER BY class_sessions.start_time
    """)

    data = cursor.fetchall()

    for session in data:
        cursor.execute("""
            SELECT topic_title
            FROM class_topics
            WHERE class_session_id = ?
            ORDER BY id
        """, (session["id"],))

        topics = cursor.fetchall()
        session["topics"] = [topic["topic_title"] for topic in topics]

        total = session["total_students"] or 0
        present = session["present_count"] or 0

        session["absent_count"] = max(total - present, 0)
        session["attendance_percentage"] = round((present / total) * 100, 1) if total > 0 else 0

    cursor.close()
    conn.close()

    return data

def mark_class_not_conducted(session_id, remarks=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE class_sessions
        SET status = 'Not Conducted',
            remarks = ?
        WHERE id = ?
    """, (remarks, session_id))

    conn.commit()

    cursor.close()
    conn.close()

def create_extra_class(section_id, subject_id, faculty_id, session_date, start_time, end_time, remarks=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO class_sessions (
            schedule_id, section_id, subject_id, scheduled_faculty_id,
            actual_faculty_id, session_date, start_time, end_time,
            session_type, status, remarks
        )
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, 'Extra', 'Conducted', ?)
    """, (section_id, subject_id, faculty_id, faculty_id, session_date, start_time, end_time, remarks))

    conn.commit()
    session_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return session_id


def get_dashboard_semester_data():
    conn = get_connection()
    cursor = conn.cursor()

    semester_numbers = [2, 4, 6, 8]
    data = []

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    today_day = days[datetime.now().weekday()]
    now_time = datetime.now().strftime("%H:%M:%S")

    for sem_no in semester_numbers:
        cursor.execute("""
            SELECT id
            FROM semesters
            WHERE semester_no = ?
        """, (sem_no,))

        semester = cursor.fetchone()

        if not semester:
            data.append({
                "semester_no": sem_no,
                "sections_data": []
            })
            continue

        cursor.execute("""
            SELECT id, name
            FROM sections
            WHERE semester_id = ?
            ORDER BY name
        """, (semester["id"],))

        sections = cursor.fetchall()
        sections_data = []

        for section in sections:
            section_id = section["id"]

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM students
                WHERE section_id = ?
            """, (section_id,))
            total_students = cursor.fetchone()["total"]

            # SQLite compatible CURDATE() mapping
            cursor.execute("""
                SELECT COUNT(DISTINCT student_id) AS present
                FROM attendance
                WHERE section_id = ?
                AND date = date('now', 'localtime')
                AND status IN ('Present', 'Late')
            """, (section_id,))
            present_today = cursor.fetchone()["present"]

            cursor.execute("""
                SELECT
                    schedule.id,
                    subjects.name AS subject_name,
                    faculty.name AS teacher,
                    sections.name AS section_name,
                    schedule.start_time,
                    schedule.end_time,
                    COUNT(DISTINCT attendance.student_id) AS present_count
                FROM schedule
                JOIN subjects ON schedule.subject_id = subjects.id
                JOIN faculty ON schedule.faculty_id = faculty.id
                JOIN sections ON schedule.section_id = sections.id
                LEFT JOIN attendance
                    ON attendance.schedule_id = schedule.id
                    AND attendance.date = date('now', 'localtime')
                    AND attendance.status IN ('Present', 'Late')
                WHERE schedule.section_id = ?
                AND schedule.day = ?
                GROUP BY
                    schedule.id, subjects.name, faculty.name, sections.name, schedule.start_time, schedule.end_time
                ORDER BY schedule.start_time
            """, (section_id, today_day))
            schedules = cursor.fetchall()

            cursor.execute("""
                SELECT
                    schedule.id,
                    subjects.name AS subject_name,
                    faculty.name AS teacher,
                    sections.name AS section_name,
                    schedule.start_time,
                    schedule.end_time
                FROM schedule
                JOIN subjects ON schedule.subject_id = subjects.id
                JOIN faculty ON schedule.faculty_id = faculty.id
                JOIN sections ON schedule.section_id = sections.id
                WHERE schedule.section_id = ?
                AND schedule.day = ?
                AND ? BETWEEN schedule.start_time AND schedule.end_time
                ORDER BY schedule.start_time
            """, (section_id, today_day, now_time))
            current_classes = cursor.fetchall()

            sections_data.append({
                "section_id": section_id,
                "section_name": section["name"],
                "total_students": total_students,
                "present_today": present_today,
                "current_classes": current_classes,
                "schedules": schedules
            })

        data.append({
            "semester_no": sem_no,
            "sections_data": sections_data
        })

    cursor.close()
    conn.close()

    return data

def get_daily_attendance_sheet(date, section_id, subject_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, roll_no
        FROM students
        WHERE section_id = ?
        ORDER BY roll_no
    """, (section_id,))
    students = cursor.fetchall()

    cursor.execute("""
        SELECT student_id, status
        FROM attendance
        WHERE section_id = ?
        AND subject_id = ?
        AND date = ?
    """, (section_id, subject_id, date))
    attendance_rows = cursor.fetchall()

    attendance_map = {row["student_id"]: row["status"] for row in attendance_rows}
    sheet = []

    for student in students:
        status = attendance_map.get(student["id"], "Absent")
        sheet.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "status": status
        })

    cursor.close()
    conn.close()
    return sheet

def get_monthly_attendance_sheet(year, month, section_id, subject_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, roll_no
        FROM students
        WHERE section_id = ?
        ORDER BY roll_no
    """, (section_id,))
    students = cursor.fetchall()

    # SQLite mein strftime use karke year aur month extraction karenge (MySQL ke YEAR() / MONTH() ki jagah)
    cursor.execute("""
        SELECT id, session_date, start_time, end_time
        FROM class_sessions
        WHERE section_id = ?
        AND subject_id = ?
        AND strftime('%Y', session_date) = ?
        AND strftime('%m', session_date) = ?
        AND status = 'Conducted'
        ORDER BY session_date, start_time
    """, (section_id, subject_id, str(year), f"{int(month):02d}"))
    sessions = cursor.fetchall()

    session_ids = [s["id"] for s in sessions]
    attendance_map = {}

    if session_ids:
        placeholders = ",".join(["?"] * len(session_ids))
        cursor.execute(f"""
            SELECT student_id, class_session_id, status
            FROM attendance
            WHERE class_session_id IN ({placeholders})
        """, session_ids)
        rows = cursor.fetchall()
        for row in rows:
            attendance_map[(row["student_id"], row["class_session_id"])] = row["status"]

    sheet = []

    for student in students:
        session_statuses = []
        total_present = 0
        total_absent = 0

        for session in sessions:
            raw_status = attendance_map.get((student["id"], session["id"]), "Absent")
            if raw_status == "Present":
                short_status = "P"
                total_present += 1
            elif raw_status == "Late":
                short_status = "L-P"
                total_present += 1
            else:
                short_status = "A"
                total_absent += 1

            session_statuses.append({
                "session_id": session["id"],
                "status": short_status
            })

        total_classes = len(sessions)
        percentage = round((total_present / total_classes) * 100, 1) if total_classes > 0 else 0

        sheet.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "session_statuses": session_statuses,
            "total_present": total_present,
            "total_absent": total_absent,
            "percentage": percentage
        })

    cursor.close()
    conn.close()
    return sessions, sheet


def get_student_attendance_report(search_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            students.id, students.name, students.roll_no, semesters.semester_no, sections.name AS section_name
        FROM students
        JOIN sections ON students.section_id = sections.id
        JOIN semesters ON sections.semester_id = semesters.id
        WHERE students.name LIKE ?
        OR students.roll_no LIKE ?
        LIMIT 1
    """, (f"%{search_text}%", f"%{search_text}%"))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return None, []

    cursor.execute("""
        SELECT subjects.name AS subject_name, attendance.date, attendance.time, attendance.status, attendance.marked_by
        FROM attendance
        JOIN subjects ON attendance.subject_id = subjects.id
        WHERE attendance.student_id = ?
        ORDER BY attendance.date DESC, attendance.time DESC
    """, (student["id"],))
    records = cursor.fetchall()

    cursor.close()
    conn.close()
    return student, records


def system_health_check():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # SQLite checking syntax
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("[HEALTH CHECK FAILED]", e)
        return False
    
def get_subjects_by_semester(semester_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM subjects
        WHERE semester_id = ?
        ORDER BY name
    """, (semester_id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data

def subject_exists(subject_name, semester_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM subjects
        WHERE LOWER(name) = LOWER(?)
        AND semester_id = ?
    """, (subject_name.strip(), semester_id))
    data = cursor.fetchone()

    cursor.close()
    conn.close()
    return data is not None


def update_subject(subject_id, subject_name, semester_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE subjects
        SET name = ?, semester_id = ?
        WHERE id = ?
    """, (subject_name.strip(), semester_id, subject_id))
    conn.commit()

    cursor.close()
    conn.close()


def get_subject_by_id(subject_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, semester_id
        FROM subjects
        WHERE id = ?
    """, (subject_id,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()
    return data


def delete_subject(subject_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM subjects
        WHERE id = ?
    """, (subject_id,))
    conn.commit()

    cursor.close()
    conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, username, password, role, faculty_id, is_active
        FROM users
        WHERE username = ?
        AND is_active = 1
    """, (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()
    return user

def get_teacher_today_classes(faculty_id, today_day):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sc.id, sc.day, sc.start_time, sc.end_time, sub.name AS subject_name, sem.semester_no, sec.name AS section_name
        FROM schedule sc
        JOIN subjects sub ON sc.subject_id = sub.id
        JOIN sections sec ON sc.section_id = sec.id
        JOIN semesters sem ON sec.semester_id = sem.id
        WHERE sc.faculty_id = ?
        AND sc.day = ?
        ORDER BY sc.start_time
    """, (faculty_id, today_day))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data

def get_students_for_teacher_current_class(faculty_id):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    today_day = now.strftime("%a").upper()   # MON, TUE, WED...
    current_time = now.strftime("%H:%M:%S")

    cursor.execute("""
        SELECT
            sc.id AS schedule_id, sc.section_id, sc.subject_id, sub.name AS subject_name,
            f.name AS teacher_name, sem.semester_no, sec.name AS section_name, sc.start_time, sc.end_time
        FROM schedule sc
        JOIN subjects sub ON sc.subject_id = sub.id
        JOIN faculty f ON sc.faculty_id = f.id
        JOIN sections sec ON sc.section_id = sec.id
        JOIN semesters sem ON sec.semester_id = sem.id
        WHERE sc.faculty_id = ?
        AND sc.day = ?
        AND sc.start_time <= ?
        AND sc.end_time >= ?
        LIMIT 1
    """, (faculty_id, today_day, current_time, current_time))
    current_class = cursor.fetchone()

    if not current_class:
        cursor.close()
        conn.close()
        return None, []

    cursor.execute("""
        SELECT id, name, roll_no, gender
        FROM students
        WHERE section_id = ?
        ORDER BY roll_no
    """, (current_class["section_id"],))
    students = cursor.fetchall()

    cursor.close()
    conn.close()
    return current_class, students

def get_teacher_dashboard_data(faculty_id, today_day):
    conn = get_connection()
    cursor = conn.cursor()

    now_time = datetime.now().strftime("%H:%M:%S")

    cursor.execute("""
        SELECT sc.id, sc.day, sc.start_time, sc.end_time, sub.name AS subject_name, sem.semester_no, sec.name AS section_name
        FROM schedule sc
        JOIN subjects sub ON sc.subject_id = sub.id
        JOIN sections sec ON sc.section_id = sec.id
        JOIN semesters sem ON sec.semester_id = sem.id
        WHERE sc.faculty_id = ?
        AND sc.day = ?
        ORDER BY sc.start_time
    """, (faculty_id, today_day))
    today_schedule = cursor.fetchall()

    active_class = None
    for cls in today_schedule:
        start_time = str(cls["start_time"])
        end_time = str(cls["end_time"])
        if start_time <= now_time <= end_time:
            active_class = cls
            break

    cursor.close()
    conn.close()
    return active_class, today_schedule

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.name, u.username, u.password, u.role, u.faculty_id, u.is_active, f.name AS faculty_name
        FROM users u
        LEFT JOIN faculty f ON u.faculty_id = f.id
        ORDER BY u.role, u.name
    """)
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data


def add_user(name, username, password, role, faculty_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, username, password, role, faculty_id, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (name, username, password, role, faculty_id))
    conn.commit()

    cursor.close()
    conn.close()


def update_user(user_id, name, username, role, faculty_id, is_active):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET name = ?, username = ?, role = ?, faculty_id = ?, is_active = ?
        WHERE id = ?
    """, (name, username, role, faculty_id, is_active, user_id))
    conn.commit()

    cursor.close()
    conn.close()


def reset_user_password(user_id, new_password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password = ?
        WHERE id = ?
    """, (new_password, user_id))
    conn.commit()

    cursor.close()
    conn.close()


def deactivate_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_active = 0
        WHERE id = ?
    """, (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

def add_class_topics(class_session_id, topics):
    conn = get_connection()
    cursor = conn.cursor()

    for topic in topics:
        topic = topic.strip()
        if topic:
            cursor.execute("""
                INSERT INTO class_topics (class_session_id, topic_title)
                VALUES (?, ?)
            """, (class_session_id, topic))

    conn.commit()
    cursor.close()
    conn.close()


def get_topics_by_class_session(class_session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic_title
        FROM class_topics
        WHERE class_session_id = ?
        ORDER BY id
    """, (class_session_id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data

def create_or_get_class_session(schedule_id):
    schedule = get_schedule_by_id(schedule_id)
    if not schedule:
        return None

    return create_class_session(
        schedule_id=schedule_id,
        section_id=schedule["section_id"],
        subject_id=schedule["subject_id"],
        scheduled_faculty_id=schedule["faculty_id"],
        actual_faculty_id=schedule["faculty_id"],
        session_date=datetime.now().strftime("%Y-%m-%d"),
        start_time=schedule["start_time"],
        end_time=schedule["end_time"],
        session_type="Scheduled",
        status="Conducted",
        remarks=None
    )

def get_existing_class_session(schedule_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM class_sessions
        WHERE schedule_id = ?
        AND session_date = date('now', 'localtime')
        AND status = 'Conducted'
        ORDER BY id DESC
        LIMIT 1
    """, (schedule_id,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()
    return data

def get_teacher_attendance_records(faculty_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cs.id, cs.session_date, cs.start_time, cs.end_time, cs.session_type, cs.status, cs.remarks,
            sub.name AS subject_name, sem.semester_no, sec.name AS section_name,
            COUNT(DISTINCT st.id) AS total_students,
            COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late', 'Late Present') THEN a.student_id END) AS present_count
        FROM class_sessions cs
        JOIN subjects sub ON cs.subject_id = sub.id
        JOIN sections sec ON cs.section_id = sec.id
        JOIN semesters sem ON sec.semester_id = sem.id
        LEFT JOIN students st ON st.section_id = cs.section_id
        LEFT JOIN attendance a ON a.class_session_id = cs.id
        WHERE cs.actual_faculty_id = ? or cs.scheduled_faculty_id = ?
        GROUP BY
            cs.id, cs.session_date, cs.start_time, cs.end_time, cs.session_type, cs.status, cs.remarks,
            sub.name, sem.semester_no, sec.name
        ORDER BY cs.session_date DESC, cs.start_time DESC
    """, (faculty_id, faculty_id))
    records = cursor.fetchall()

    for record in records:
        total = record["total_students"] or 0
        present = record["present_count"] or 0

        record["absent_count"] = max(total - present, 0)
        record["attendance_percentage"] = round((present / total) * 100, 1) if total > 0 else 0

        cursor.execute("""
            SELECT topic_title
            FROM class_topics
            WHERE class_session_id = ?
            ORDER BY id
        """, (record["id"],))
        topics = cursor.fetchall()
        record["topics"] = [t["topic_title"] for t in topics]

        student_attendance = get_class_session_student_attendance(record["id"])
        record["present_students"] = [s for s in student_attendance if s["status"] in ("Present", "Late", "Late Present")]
        record["absent_students"] = [s for s in student_attendance if s["status"] not in ("Present", "Late", "Late Present")]

    cursor.close()
    conn.close()
    return records

def get_class_session_student_attendance(class_session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cs.section_id
        FROM class_sessions cs
        WHERE cs.id = ?
    """, (class_session_id,))
    session_data = cursor.fetchone()

    if not session_data:
        cursor.close()
        conn.close()
        return []

    section_id = session_data["section_id"]

    cursor.execute("""
        SELECT st.id AS student_id, st.name, st.roll_no, COALESCE(a.status, 'Absent') AS status
        FROM students st
        LEFT JOIN attendance a ON a.student_id = st.id AND a.class_session_id = ?
        WHERE st.section_id = ?
        ORDER BY st.roll_no
    """, (class_session_id, section_id))
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data