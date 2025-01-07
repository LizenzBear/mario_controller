# Mario Pose Controller mit PyQt und Mediapipe 🎮🕹️
Dieses Projekt kombiniert **OpenCV**, **Mediapipe** und **PyQt**, um eine benutzerfreundliche Oberfläche bereitzustellen, mit der eine Kamera Bewegungen erkennt und interpretiert.

---

## Projektbeschreibung 📋
### Kernfunktionen

1. **Kamera-Feed**:
   - Der Kamerastream wird live angezeigt.
   - Im Videostream werden **Linien** für Bewegungsgrenzen (Stoppen, Springen) eingezeichnet.

2. **Bewegungserkennung**:
   - Mithilfe von **Mediapipe Pose Detection** erkennt das Programm Bewegungen.
   - Gesten wie **Springen**, **Bewegen links/rechts** und **Stoppen** werden interpretiert.

3. **Anzeige von Gesten und Fehlern**:
   - **Gesten** wie "Jumping", "Moving Left" oder "Stopped" werden **unterhalb des Kamerastreams** angezeigt.
   - **Fehlermeldungen** (z. B. "Oberkörper nicht sichtbar") erscheinen **über den Gesten**.

4. **Steuerung**:
   - Das Programm simuliert Tasteneingaben wie "W" (Springen), "A" (Links) und "D" (Rechts) und kann so Spiele wie [Super Mario Play](https://supermarioplay.com/fullscreen) steuern.

---

## Voraussetzungen ⚙️
### Installierte Pakete
Das Programm benötigt **Python 3.12** und folgende Bibliotheken:
```bash
pip install PyQt5 opencv-python mediapipe pyautogui numpy
```
Alternativ:
```bash
pip install -r requirements.txt
```

### Betriebssysteme
- Windows, macOS oder Linux

---

## Projektstart 🚀
1. **Repository klonen**:
    ```bash
    git clone https://github.com/LizenzBear/mario_controller
    cd mario_controller
    ```

2. **Benötigte Pakete installieren**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Programm starten**:
    ```bash
    python main.py
    ```

4. **Kamera einschalten** und sicherstellen, dass dein **Oberkörper sichtbar** ist.

---

## Wichtige Codeabschnitte 💻

### 1. Kamera-Initialisierung
Die Kamera wird mit OpenCV geöffnet, und Mediapipe wird vorbereitet, um Körperlandmarks zu erkennen. Die Schleife liest jeden Frame, verarbeitet ihn und gibt die Ergebnisse zurück:
```python
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
        if results.pose_landmarks:
            self.process_landmarks(results.pose_landmarks.landmark, frame_height, frame_width)
```

### 2. Verarbeitung der Landmarks
Die erkannten Landmarks werden analysiert, um Gesten wie "Springen", "Stoppen" oder Richtungsänderungen zu identifizieren:
```python
def process_landmarks(self, landmark_list, frame_height, frame_width):
    if self.in_frame(landmark_list):
        self.update_movement(landmark_list, frame_height)
        self.calibrate(landmark_list)
        self.detect_direction(landmark_list, frame_width)
        self.detect_stop(landmark_list)
        self.detect_jump(landmark_list)

        if not self.stop_detected:
            self.handle_movement()
        else:
            self.current_gesture = "Stopped"
    else:
        self.error_changed.emit("Make sure your upper body is fully visible")
```

### 3. Bewegungserkennung: "Springen"
Wenn die Position der Nase (Landmark 0) über einer bestimmten Schwelle liegt, wird die Sprungaktion ausgelöst:
```python
def detect_jump(self, landmark_list):
    if landmark_list[0].y < self.jump_threshold and not self.press_space:
        self.press_space = True
        self.start_time = time.time()
        pyautogui.keyDown("space")
        self.current_gesture = "Jumping"
```

### 4. Bewegungserkennung: "Stoppen"
Die Y-Position der Handgelenke wird überwacht. Wenn beide über einer bestimmten Schwelle liegen, wird "Stopped" ausgelöst:
```python
def detect_stop(self, landmark_list):
    if (landmark_list[15].y > self.stop_threshold) and (landmark_list[16].y > self.stop_threshold):
        if self.key_pressed:
            pyautogui.keyUp(self.key_pressed)
            self.key_pressed = ""
        self.current_gesture = "Stopped"
        self.stop_detected = True
    else:
        self.stop_detected = False
```

### 5. Richtungsbestimmung
Die X-Koordinaten der Nase und der Schultern werden gemittelt, um festzustellen, ob sich der Spieler nach links oder rechts bewegt:
```python
def detect_direction(self, landmark_list, frame_width):
    landmarks_to_use = [landmark_list[0], landmark_list[11], landmark_list[12]]
    average_x = sum(landmark.x for landmark in landmarks_to_use) / len(landmarks_to_use)
    self.average_x_in_pixels = average_x * frame_width

    if self.average_x_in_pixels < frame_width / 2:
        self.direction = "left"
    else:
        self.direction = "right"
```

### 6. Kalibrierung
Falls wenig Bewegung erkannt wird, werden die Schwellenwerte angepasst:
```python
def calibrate(self, landmark_list):
    if np.sum(self.movement_history) < self.calibration_movement_threshold:
        nose_y = landmark_list[0].y
        left_hip_y = landmark_list[23].y
        right_hip_y = landmark_list[24].y
        average_hip_y = (left_hip_y + right_hip_y) / 2
        self.stop_threshold = average_hip_y - 0.05
        self.jump_threshold = nose_y - 0.05
```

### 7. Zeichnen der visuellen Hilfen
Linien für Bewegungsgrenzen und die Mittelachse werden gezeichnet:
```python
cv2.line(
    frame,
    (0, int(self.stop_threshold * frame_height)),
    (frame_width, int(self.stop_threshold * frame_height)),
    (0, 0, 255),  # Rote Linie für Stop
    2,
)
cv2.line(
    frame,
    (0, int(self.jump_threshold * frame_height)),
    (frame_width, int(self.jump_threshold * frame_height)),
    (255, 0, 0),  # Blaue Linie für Jump
    2,
)
cv2.line(
    frame,
    (frame_width // 2, 0),
    (frame_width // 2, frame_height),
    (0, 255, 0),  # Grüne Linie für die Mittelachse
    2,
)
```

---

## Integration mit PyQt 🖥️
Die Integration mit **PyQt** ermöglicht die Darstellung des Kamerastreams, der Gesten und der Fehlermeldungen in einer GUI. Die Hauptklasse `MainWindow` definiert die Benutzeroberfläche:

### 1. Aufbau der Benutzeroberfläche
Es wird ein Hauptfenster mit drei Bereichen erstellt:
- **Kamerastream**
- **Fehlermeldungen**
- **Gestenanzeige**
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mario Pose Controller")
        self.resize(1280, 720)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        # Kameraansicht
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label, stretch=5)

        # Fehlermeldungen
        self.error_label = QLabel("")
        font = QFont()
        font.setPointSize(20)
        self.error_label.setFont(font)
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label, stretch=1)

        # Gestenanzeige
        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setFont(font)
        self.gesture_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.gesture_label, stretch=1)
```

### 2. Verknüpfung mit dem Kamerathread
Der Kamerathread verarbeitet die Frames und sendet Signale für das Update der GUI:
```python
self.controller_thread = MarioControllerThread()
self.controller_thread.frame_ready.connect(self.update_frame)
self.controller_thread.gesture_changed.connect(self.update_gesture)
self.controller_thread.error_changed.connect(self.update_error)
self.controller_thread.start()
```

### 3. Aktualisierung der GUI-Elemente
Die folgenden Funktionen aktualisieren den Kamerastream, die Gestenanzeige und die Fehlermeldungen:
```python
def update_frame(self, frame: np.ndarray):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_frame.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qimg)
    self.video_label.setPixmap(pixmap)

def update_gesture(self, gesture: str):
    self.gesture_label.setText(f"Gesture: {gesture}")

def update_error(self, msg: str):
    self.error_label.setText(msg)
```

### 4. Programmstart
Das Hauptfenster wird durch die `main()`-Funktion gestartet:
```python
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

---

## Verwendung 🕹️
1. **Bewege deinen Oberkörper** innerhalb des Kamerafeldes:
    - **Links bewegen**: Das Programm erkennt die Bewegung nach links und simuliert "A".
    - **Rechts bewegen**: Bewegung nach rechts simuliert "D".
    - **Springen**: Hebe deinen Kopf, um zu springen ("Space").
    - **Stillstehen**: Keine Bewegung führt zur Anzeige von "Stopped".

2. **Fehlermeldungen**:
    - Wenn dein Oberkörper nicht vollständig sichtbar ist, erscheint die Meldung **"Make sure your upper body is fully visible"**.

