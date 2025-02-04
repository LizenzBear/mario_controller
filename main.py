import sys
import time

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


class MarioControllerThread(QThread):
    """
    Thread capturing camera frames, running pose detection,
    drawing only threshold lines on the frames,
    and emitting signals for (frame + current gesture + error/warning).
    """

    frame_ready = pyqtSignal(np.ndarray)  # Signal with the processed video frame
    gesture_changed = pyqtSignal(str)  # Signal with the current gesture string
    error_changed = pyqtSignal(str)  # Signal with the error/warning message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.history_length = 5
        self.diff_threshold = self.history_length * 40
        self.movement_history = np.zeros((self.history_length,))
        self.stop_threshold = 0.8
        self.jump_threshold = 0.2
        self.jump_duration = 0.5
        self.prev_height = 0
        self.new_height = 0
        self.key_pressed = ""
        self.press_space = False
        self.start_time = 0
        self.stop_detected = False
        self.direction = "right"
        self.average_x_in_pixels = 0
        self.pose = mp.solutions.pose.Pose()
        self.drawing_utils = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set desired width
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)  # Set desired height

        self.current_gesture = "None"
        self.calibration_movement_threshold = 50

    def stop(self):
        self.running = False

    def in_frame(self, landmark_list):
        return (
            (landmark_list[0].visibility > 0.7)
            and (landmark_list[15].visibility > 0.7)
            and (landmark_list[16].visibility > 0.7)
        )

    def update_movement(self, landmark_list, frame_height):
        self.new_height = sum(landmark.y * frame_height for landmark in landmark_list)
        self.movement_history[1:] = self.movement_history[:-1]
        self.movement_history[0] = abs(self.new_height - self.prev_height)
        self.prev_height = self.new_height

    def detect_jump(self, landmark_list):
        if landmark_list[0].y < self.jump_threshold and not self.press_space:
            self.press_space = True
            self.start_time = time.time()
            pyautogui.keyDown("space")
            self.current_gesture = "Jumping"

    def release_jump(self):
        if (time.time() - self.start_time) > self.jump_duration:
            pyautogui.keyUp("space")
            self.press_space = False
            self.current_gesture = "None"

    def detect_stop(self, landmark_list):
        if (landmark_list[15].y > self.stop_threshold) and (
            landmark_list[16].y > self.stop_threshold
        ):
            if self.key_pressed:
                pyautogui.keyUp(self.key_pressed)
                self.movement_history = np.zeros((self.history_length,))
                self.key_pressed = ""
                self.current_gesture = "Stopped"
            self.stop_detected = True
        else:
            self.stop_detected = False

    def detect_direction(self, landmark_list, frame_width):
        # Use Nose(0), Left Shoulder(11), Right Shoulder(12)
        landmarks_to_use = [
            landmark_list[0],
            landmark_list[11],
            landmark_list[12],
        ]
        average_x = sum(landmark.x for landmark in landmarks_to_use) / len(
            landmarks_to_use
        )
        self.average_x_in_pixels = average_x * frame_width

        if self.average_x_in_pixels < frame_width / 2:
            self.direction = "left"
        else:
            self.direction = "right"

    def handle_movement(self):
        if np.sum(self.movement_history) > self.diff_threshold:
            if self.direction == "left":
                if self.key_pressed != "a":
                    if self.key_pressed:
                        pyautogui.keyUp(self.key_pressed)
                    pyautogui.keyDown("a")
                    self.key_pressed = "a"
                    self.current_gesture = "Moving Left"
            elif self.direction == "right":
                if self.key_pressed != "d":
                    if self.key_pressed:
                        pyautogui.keyUp(self.key_pressed)
                    pyautogui.keyDown("d")
                    self.key_pressed = "d"
                    self.current_gesture = "Moving Right"
        else:
            if self.key_pressed:
                pyautogui.keyUp(self.key_pressed)
                self.key_pressed = ""
                self.current_gesture = "Stopped"

    def calibrate(self, landmark_list):
        # If not moving much, recalibrate the thresholds
        if np.sum(self.movement_history) < self.calibration_movement_threshold:
            nose_y = landmark_list[0].y
            left_hip_y = landmark_list[23].y
            right_hip_y = landmark_list[24].y

            average_hip_y = (left_hip_y + right_hip_y) / 2
            self.stop_threshold = average_hip_y - 0.05
            self.jump_threshold = nose_y - 0.05

            self.stop_threshold = min(max(self.stop_threshold, 0), 1)
            self.jump_threshold = min(max(self.jump_threshold, 0), 1)

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.blur(frame, (5, 5))

            results = self.pose.process(rgb_frame)
            error_message = ""

            if results.pose_landmarks:
                self.drawing_utils.draw_landmarks(
                    frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS
                )
                if self.in_frame(results.pose_landmarks.landmark):
                    self.update_movement(results.pose_landmarks.landmark, frame_height)
                    self.calibrate(results.pose_landmarks.landmark)
                    self.detect_direction(results.pose_landmarks.landmark, frame_width)
                    self.detect_stop(results.pose_landmarks.landmark)
                    self.detect_jump(results.pose_landmarks.landmark)
                    if not self.stop_detected:
                        self.handle_movement()
                        if self.press_space:
                            self.release_jump()
                    else:
                        self.current_gesture = "Stopped"
                else:
                    # The "upper body not fully visible" message
                    error_message = "Make sure your upper body is fully visible"
            else:
                # No landmarks found at all
                error_message = "No pose landmarks detected"

            # Draw threshold lines on the frame
            cv2.line(
                frame,
                (0, int(self.stop_threshold * frame_height)),
                (frame_width, int(self.stop_threshold * frame_height)),
                (0, 0, 255),
                2,
            )
            cv2.line(
                frame,
                (0, int(self.jump_threshold * frame_height)),
                (frame_width, int(self.jump_threshold * frame_height)),
                (255, 0, 0),
                2,
            )
            cv2.line(
                frame,
                (frame_width // 2, 0),
                (frame_width // 2, frame_height),
                (0, 255, 0),
                2,
            )

            # Minimal text on the frame
            cv2.putText(
                frame,
                "Threshold lines only",
                (30, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
            )

            # Emit the frame
            self.frame_ready.emit(frame)

            # Emit the current gesture and error messages
            self.gesture_changed.emit(
                self.current_gesture if self.current_gesture else "None"
            )
            self.error_changed.emit(error_message)

        self.cap.release()


from PyQt5.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Mario Pose Controller - Lines in Frame, Errors & Gestures in UI"
        )
        self.resize(1280, 720)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        # Camera feed (top)
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label, stretch=2)

        # Error message label (middle)
        self.error_label = QLabel("")
        font40 = QFont()
        font40.setPointSize(40)
        font40.setBold(True)

        self.error_label.setFont(font40)
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label, stretch=1)

        # Gesture label (bottom)
        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setFont(font40)
        self.gesture_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.gesture_label, stretch=1)

        # Start the MarioController logic in a separate thread
        self.controller_thread = MarioControllerThread()
        self.controller_thread.frame_ready.connect(self.update_frame)
        self.controller_thread.gesture_changed.connect(self.update_gesture)
        self.controller_thread.error_changed.connect(self.update_error)
        self.controller_thread.start()

    def update_frame(self, frame: np.ndarray):
        # Convert the OpenCV BGR frame to a QPixmap for display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def update_gesture(self, gesture: str):
        # If gesture is "None", we can show "Gesture: None" or be empty
        if gesture == "None":
            self.gesture_label.setText("Gesture: None")
        elif gesture == "Stopped":
            self.gesture_label.setText("Gesture: Stopped ■")
        elif gesture == "Jumping":
            self.gesture_label.setText("Gesture: Jumping ↑")
        elif gesture == "Moving Left":
            self.gesture_label.setText("Gesture: Moving Left ←")
        elif gesture == "Moving Right":
            self.gesture_label.setText("Gesture: Moving Right →")
        else:
            self.gesture_label.setText(f"Gesture: {gesture}")

    def update_error(self, msg: str):
        """Show any error/warning messages above the gesture label."""
        # If empty message, no error
        if msg:
            self.error_label.setText(msg)
        else:
            self.error_label.setText("")

    def closeEvent(self, event):
        self.controller_thread.stop()
        self.controller_thread.wait(timeout=2000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
