import os
import cv2
import numpy as np
from datetime import datetime
from deepface import DeepFace

from database import (
    get_all_students,
    get_students_by_section,
    get_connection,
    create_class_session,
    mark_attendance_class
)

STUDENTS_FOLDER = "student_images"
# MODEL_NAME = "Facenet512"
MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "opencv"
DISTANCE_THRESHOLD = 0.40


def get_student_main_image(student):
    roll_no = student["roll_no"]
    folder = os.path.join(STUDENTS_FOLDER, str(roll_no))

    if not os.path.exists(folder):
        return None

    for file in os.listdir(folder):
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            return os.path.join(folder, file)

    return None


def verify_faces(live_face_path, student_image_path):
    try:
        result = DeepFace.verify(
            img1_path=live_face_path,
            img2_path=student_image_path,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False
        )

        return result["verified"], result["distance"]

    except Exception as e:
        print("[VERIFY ERROR]", e)
        return False, 999


def test_known_students():
    students = get_all_students()

    print("Registered students with images:")

    for student in students:
        img = get_student_main_image(student)

        if img:
            print(student["id"], student["name"], student["roll_no"], img)
        else:
            print(student["id"], student["name"], student["roll_no"], "NO IMAGE")

def start_class_attendance_engine_deepface(schedule_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sc.*,
            sub.id AS subject_id,
            sub.name AS subject_name,
            f.name AS teacher_name
        FROM schedule sc
        JOIN subjects sub ON sc.subject_id = sub.id
        JOIN faculty f ON sc.faculty_id = f.id
        WHERE sc.id = ?
    """, (schedule_id,))

    schedule = cursor.fetchone()

    cursor.close()
    conn.close()

    if not schedule:
        print("[ERROR] Schedule nahi mila!")
        return

    subject_id = schedule["subject_id"]
    section_id = schedule["section_id"]
    faculty_id = schedule["faculty_id"]

    students = get_students_by_section(section_id)

    if not students:
        print("[ERROR] Is section mein koi student nahi!")
        return

    class_session_id = create_class_session(
        schedule_id=schedule_id,
        section_id=section_id,
        subject_id=subject_id,
        scheduled_faculty_id=faculty_id,
        actual_faculty_id=faculty_id,
        session_date=datetime.now().strftime("%Y-%m-%d"),
        start_time=schedule["start_time"],
        end_time=schedule["end_time"],
        session_type="Scheduled",
        status="Conducted",
        remarks=None
    )

    allowed_students = []

    for student in students:
        img_path = get_student_main_image(student)

        if img_path:
            student["image_path"] = img_path
            allowed_students.append(student)

    if not allowed_students:
        print("[ERROR] Is class ke male/image students available nahi hain.")
        return

    print(f"[INFO] DeepFace Attendance Started")
    print(f"[INFO] Subject: {schedule['subject_name']}")
    print(f"[INFO] Teacher: {schedule.get('teacher_name', 'N/A')}")
    print(f"[INFO] Allowed students: {len(allowed_students)}")
    print("[INFO] Q press karo band karne ke liye...")

    os.makedirs("temp_faces", exist_ok=True)

    # cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    # cam = cv2.VideoCapture(0)
    cam = cv2.VideoCapture(0, cv2.CAP_MSMF)

    if not cam.isOpened():
        print("[ERROR] Camera open nahi ho saka.")
        return

    marked_in_session = set()
    frame_count = 0

    last_display_text = "Scanning..."
    last_display_color = (255, 255, 0)

    cam = cv2.VideoCapture(0)
    
    if not cam.isOpened():
        print("[ERROR] Camera open nahi ho saka.")
        return
    
    window_name = "DeepFace Attendance"
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    cv2.resizeWindow(window_name, 900, 650)


    while True:
        ret, frame = cam.read()

        if not ret:
            print("[ERROR] Camera frame read nahi hua.")
            break

        frame_count += 1

        display_text = last_display_text
        display_color = last_display_color

        # Har 20th frame par DeepFace compare karein taake system slow na ho
        # if frame_count % 20 == 0:
        if frame_count % 60 == 0:
            live_path = "temp_faces/live_face.jpg"
            cv2.imwrite(live_path, frame)

            best_student = None
            best_distance = 999

            for student in allowed_students:

                if student["id"] in marked_in_session:
                    continue
                verified, distance = verify_faces(
                    live_path,
                    student["image_path"]
                )

                print(
                    f"[CHECK] {student['name']} | Distance: {distance:.3f} | Verified: {verified}"
                )

                if distance < best_distance:
                    best_distance = distance
                    best_student = student

            if best_student and best_distance <= DISTANCE_THRESHOLD:
                student_id = best_student["id"]

                display_text = f"{best_student['name']} ({best_distance:.2f})"
                display_color = (0, 255, 0)

                last_display_text = display_text
                last_display_color = display_color

                if student_id not in marked_in_session:
                    mark_attendance_class(
                        student_id=student_id,
                        subject_id=subject_id,
                        schedule_id=schedule_id,
                        class_session_id=class_session_id,
                        status="Present"
                    )

                    marked_in_session.add(student_id)

                    print(
                        f"[✓] {best_student['name']} marked Present | Distance: {best_distance:.3f}"
                    )
                    last_display_text = f"✓ {best_student['name']} Marked"
                    last_display_color = (0, 255, 0)
                    
                    import time
                    time.sleep(1)

            else:
                display_text = f"Unknown ({best_distance:.2f})"
                display_color = (0, 0, 255)

                last_display_text = display_text
                last_display_color = display_color

        cv2.putText(
            frame,
            display_text,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            display_color,
            2
        )

        cv2.putText(
            frame,
            f"Class: {schedule['subject_name']}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "DeepFace Mode | Press Q to stop",
            (30, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 0),
            2
        )

        cv2.imshow("DeepFace Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()

    print(f"[DONE] Total marked in this session: {len(marked_in_session)}")

def register_student_face(name, roll_no):
    os.makedirs(STUDENTS_FOLDER, exist_ok=True)

    student_folder = os.path.join(STUDENTS_FOLDER, str(roll_no))
    os.makedirs(student_folder, exist_ok=True)

    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("[ERROR] Camera open nahi ho saka.")
        return None

    count = 0
    target_images = 8

    window_name = "DeepFace Student Registration"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    cv2.resizeWindow(window_name, 900, 650)

    print("[INFO] Registration camera started.")
    print("[INFO] Different angles rakho: front, left, right, close, far.")

    while count < target_images:
        ret, frame = cam.read()

        if not ret:
            break

        cv2.putText(
            frame,
            f"Capturing {count + 1}/{target_images}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Move face slightly. Press Q to cancel.",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 0),
            2
        )

        cv2.imshow(window_name, frame)

        img_path = os.path.join(student_folder, f"{count + 1}.jpg")
        cv2.imwrite(img_path, frame)
        count += 1

        cv2.waitKey(700)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()

    if count == 0:
        return None

    print(f"[SUCCESS] {count} images saved for {name}")

    return os.path.join(student_folder, "1.jpg")
    
if __name__ == "__main__":
    test_known_students()