# Mario Pose Controller mit PyQt und Mediapipe 🎮🕹️
Dieses Projekt kombiniert **OpenCV**, **Mediapipe** und **PyQt**, um eine benutzerfreundliche Oberfläche bereitzustellen, mit der eine Kamera Bewegungen erkennt und interpretiert.
## Projektbeschreibung 📋
1. **Kamera-Feed**:  
    Der Kamerastream wird live angezeigt. Auf dem Video werden **Linien** für Bewegungsgrenzen (Stoppen, Springen) gezeichnet.
    
2. **Bewegungserkennung**:  
    Mithilfe von **Mediapipe Pose Detection** erkennt das Programm deine Bewegungen. Gesten wie **„Jumping“ (Springen)** oder **„Moving Left/Right“ (Bewegen links/rechts)** werden erkannt.
    
3. **Anzeige von Gesten und Fehlern**:
    
    - **Gesten** wie „Jumping“, „Moving Left“, „Stopped“ werden **unterhalb des Kamerastreams** angezeigt.
    - **Fehlermeldungen** (z.B. "Oberkörper nicht sichtbar") erscheinen **über den Gesten**.
4. **Steuerung**:  
    Das Programm kann verwendet werden, um Tasteneingaben wie „W“ (Springen), „A“ (Links), „D“ (Rechts) in Spielen wie: https://supermarioplay.com/fullscreen zu simulieren.
    
---
## Voraussetzungen ⚙️
### Installierte Pakete:
Das Programm benötigt **Python 3.12** und folgende Bibliotheken:
```bash
pip install PyQt5 opencv-python mediapipe pyautogui numpy
```
oder:
```bash
pip install -r requirements.txt
```
### Betriebssystem:
- Windows, macOS oder Linux
---
## Projektstart 🚀
1. **Repository klonen**:
    ```bash
    git clone https://github.com/LizenzBear/mario_controller
    cd mario_controller
    ```
    
2. **Installiere die benötigten Pakete**:
    
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
### 1. Logik für Gestenerkennung
Die Gestenerkennung prüft die Positionen der Mediapipe-Landmarks und erkennt Gesten wie **Springen**, **Bewegen links/rechts** oder **Stoppen**:
```python
def detect_jump(self, landmark_list):
    if landmark_list[0].y < self.jump_threshold and not self.press_space:
        self.press_space = True
        self.start_time = time.time()
        pyautogui.keyDown("space")
        self.current_gesture = "Jumping"
def detect_stop(self, landmark_list):
    if (landmark_list[15].y > self.stop_threshold) and (landmark_list[16].y > self.stop_threshold):
        if self.key_pressed:
            pyautogui.keyUp(self.key_pressed)
            self.key_pressed = ""
            self.current_gesture = "Stopped"
        self.stop_detected = True
    else:
        self.stop_detected = False
def detect_direction(self, landmark_list, frame_width):
    landmarks_to_use = [landmark_list[0], landmark_list[11], landmark_list[12]]  # Nase, Schultern
    average_x = sum(landmark.x for landmark in landmarks_to_use) / len(landmarks_to_use)
    self.average_x_in_pixels = average_x * frame_width
    if self.average_x_in_pixels < frame_width / 2:
        self.direction = "left"
    else:
        self.direction = "right"
```
---
### 2. Logik zur Kalibrierung
Die Kalibrierung passt die Schwellenwerte für **Stoppen** und **Springen** dynamisch an, wenn wenig Bewegung erkannt wird:
```python
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
```
---
### 3. OpenCV: Linien für Bewegungsgrenzen
In der `run`-Methode werden Linien für **Stoppen** und **Springen** auf das Kamerabild gezeichnet:
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
### 4. Anzeige von Fehlern und Gesten in PyQt
Die Fehler und Gesten werden in der Benutzeroberfläche angezeigt und nicht auf dem Kamerastream:
```python
# Fehleranzeige über dem Gestenbereich
self.error_label = QLabel("")
self.error_label.setFont(font40)
self.error_label.setAlignment(Qt.AlignCenter)
# Gestenanzeige
self.gesture_label = QLabel("Gesture: None")
self.gesture_label.setFont(font40)
self.gesture_label.setAlignment(Qt.AlignCenter)
```
---
## Verwendung 🕹️
1. **Bewege deinen Oberkörper** innerhalb des Kamerafeldes:
    - **Links bewegen**: Das Programm erkennt die Bewegung nach links und simuliert „A“.
    - **Rechts bewegen**: Bewegung nach rechts simuliert „D“.
    - **Springen**: Hebe deinen Kopf, um zu springen („Space“).
    - **Stillstehen**: Keine Bewegung führt zur Anzeige von „Stopped“.
2. **Fehlermeldungen**:
    - Wenn dein Oberkörper nicht vollständig sichtbar ist, erscheint die Meldung **„Make sure your upper body is fully visible“**.
---
## Projektstart im Überblick 🏁
- Starte das Programm mit `python main.py`.
- Stelle sicher, dass dein Oberkörper sichtbar ist.
- Bewege dich vor der Kamera, um die Gestenerkennung zu testen.