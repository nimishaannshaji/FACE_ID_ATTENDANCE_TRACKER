from tkinter import*
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import os
import numpy as np
from datetime import datetime
import pyttsx3
import face_recognition
from threading import Thread
from PIL import Image, ImageTk

root = tk.Tk()
root.title("FACE RECOGNITION ATTENDANCE SYSTEM")
root.geometry("800x800")
root.config(bg="black")

title_label = tk.Label(root, text="FACE RECOGNITION ATTENDANCE SYSTEM",bg="black",fg="white", font=("Arial", 14, "bold"))
title_label.pack(pady=10)



# Initialize pyttsx3 engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# Load images and class names
path = 'AttendanceImg'
images = []
className = []
myList = os.listdir(path)
for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    if curImg is not None:
        images.append(curImg)
        className.append(os.path.splitext(cl)[0])

# Global variables
n_rows = 0
n_cols = 2
matrix = []

def rollnumber(name):
    for i in range(n_rows):
        if matrix[i][0] == name:
            return matrix[i][1]
    return -1


def late(hour, minute):
    now = datetime.now()
    today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return "on time" if today > now else "late"


def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList


def markAttendance(name, hour, minute, attendance_list):
    with open('Attendance.csv', 'r+') as f:
        myDataList = f.readlines()
        nameList = [line.split(',')[0] for line in myDataList]
        if name not in nameList:
            now = datetime.now()
            dt_string = now.strftime("%H:%M:%S")
            f.writelines(f'\n{name},{dt_string},{rollnumber(name)},{late(hour, minute)}')
            speak(name)
            speak('Your attendance is marked. Your Roll number is ')
            speak(rollnumber(name))
            speak('You are ')
            speak(late(hour, minute))
            
            # Update the attendance list in the GUI
            attendance_list.insert("", "end", values=(
                len(attendance_list.get_children()) + 1,  # S No
                name,  # Name
                rollnumber(name),  # Roll Number
                dt_string,  # Time
                late(hour, minute)  # Status
            ))


def faceRecognitionThread(hour, minute, attendance_list):
    encodeListKnown = findEncodings(images)
    cap = cv2.VideoCapture(0)
    while True:
        success, img = cap.read()
        if not success:
            break
        imgS = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)
            if faceDis[matchIndex] < 0.50:
                name = className[matchIndex].upper()
                markAttendance(name, hour, minute, attendance_list)  # Pass attendance_list
                speak('I recognize you as student. You are in the university database.')
            else:
                name = 'Unknown'
                speak('I do not recognize you. You are not in the database.')
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Webcam', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


def uploadImage():
    student_name = new_user_name.get()
    if not student_name:
        messagebox.showerror("Error", "Please enter a student name.")
        return
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", ".jpg;.jpeg;*.png")])
    if file_path:
        save_path = os.path.join(path, f"{student_name}.jpg")
        img = Image.open(file_path)
        img.save(save_path)
        messagebox.showinfo("Success", f"Image saved as {save_path}")


def take_attendance():
    current_time = datetime.now().strftime('%H:%M:%S')
    print("Current Time:", current_time)  # Debugging line
    attendance_list.insert("", "end", values=(
        len(attendance_list.get_children()) + 1,  # S No
        "Sample User",  # Name
        "1",  # Placeholder Roll Number
        current_time  # Time
    ))

def submitDetails():
    thread = Thread(target=faceRecognitionThread, args=(8, 0, attendance_list))  # Pass attendance_list
    thread.daemon = True
    thread.start()
    messagebox.showinfo("Details Submitted", "Face recognition started.")


new_user_frame = ttk.LabelFrame(root, text="Add New User")
new_user_frame.pack(pady=10, padx=10, fill="both", expand=True)
new_user_name = ttk.Entry(new_user_frame)
new_user_name.pack(pady=5)
add_user_btn = ttk.Button(new_user_frame, text="Upload Image",command=uploadImage)
add_user_btn.pack(pady=5)
submit_button = ttk.Button(new_user_frame, text="Start Recognition", command=submitDetails)
submit_button.pack(pady=5)



attendance_frame = ttk.LabelFrame(root, text="Today's Attendance")
attendance_frame.pack(pady=10, padx=10, fill="both", expand=True)
attendance_list = ttk.Treeview(attendance_frame, columns=("S No", "Name", "ID", "Time"), show="headings")
for col in ("S No", "Name", "ID", "Time"):
    attendance_list.heading(col, text=col)
attendance_list.pack(pady=5)

take_attendance_btn = ttk.Button(attendance_frame, text="Take Attendance", command=take_attendance)
take_attendance_btn.pack(pady=5)



root.mainloop()