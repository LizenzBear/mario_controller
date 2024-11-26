import time
import cv2
import mediapipe as mp
import numpy as np
import pyautogui

class MarioController:
    def __init__(self):
        self.history_length = 5
        self.diff_threshold = self.history_length * 40
        self.movement_history = np.zeros((self.history_length,))
        self.stop_threshold = 0.8
        self.jump_threshold = 0.2
        self.jump_duration = 0.5
        self.prev_height = 0
        self.new_height = 0
        self.key_pressed = False
        self.press_space = False
        self.start_time = 0
        self.stop_detected = False
        self.pose = mp.solutions.pose.Pose()
        self.drawing_utils = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.current_gesture = "None"
        self.calibration_movement_threshold = 50  # Adjust as needed

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
        if (landmark_list[15].y > self.stop_threshold) and (landmark_list[16].y > self.stop_threshold):
            if self.key_pressed:
                pyautogui.keyUp("d")
                pyautogui.press("a")
                self.movement_history = np.zeros((self.history_length,))
                self.key_pressed = False
                self.current_gesture = "Stopped"
            self.stop_detected = True
        else:
            self.stop_detected = False

    def handle_movement(self):
        if np.sum(self.movement_history) > self.diff_threshold:
            if not self.key_pressed:
                pyautogui.keyDown("d")
                self.key_pressed = True
                self.current_gesture = "Moving Right"
        elif self.key_pressed:
            pyautogui.keyUp("d")
            self.key_pressed = False
            self.current_gesture = "Stopped"

    def calibrate(self, landmark_list):
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
        while True:
            _, frame = self.cap.read()
            frame_height, frame_width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.blur(frame, (5, 5))
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
            results = self.pose.process(rgb_frame)
            if results.pose_landmarks:
                self.drawing_utils.draw_landmarks(
                    frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS
                )
                if self.in_frame(results.pose_landmarks.landmark):
                    self.update_movement(results.pose_landmarks.landmark, frame_height)
                    self.calibrate(results.pose_landmarks.landmark)
                    self.detect_stop(results.pose_landmarks.landmark)
                    self.detect_jump(results.pose_landmarks.landmark)
                    if not self.stop_detected:
                        self.handle_movement()
                        if self.press_space:
                            self.release_jump()
                else:
                    cv2.putText(
                        frame,
                        "You're not in frame",
                        (30, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )
            cv2.putText(
                frame,
                f"Gesture: {self.current_gesture}",
                (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2,
            )
            cv2.imshow("Pose Control Window", frame)
            if cv2.waitKey(1) == 27:
                self.cap.release()
                cv2.destroyAllWindows()
                break

if __name__ == "__main__":
    pose_controller = MarioController()
    pose_controller.run()

