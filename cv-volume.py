import cv2
import mediapipe as mp
import math
import os


def set_volume(volume_percent):
    volume_percent = max(0, min(100, int(volume_percent)))
    os.system(f"osascript -e 'set volume output volume {volume_percent}'")

# MediaPipe 
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Webcam 
cap = cv2.VideoCapture(0)

# Volume range (pixels)
min_distance = 20   
max_distance = 450    

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    vol_percent = 0  

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            lmList = handLms.landmark
            h, w, _ = img.shape

            # Thumb tip and index tip
            x1, y1 = int(lmList[4].x * w), int(lmList[4].y * h)
            x2, y2 = int(lmList[8].x * w), int(lmList[8].y * h)

            # Draw
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Distance
            length = math.hypot(x2 - x1, y2 - y1)

            # Volume
            vol_percent = (length - min_distance) / (max_distance - min_distance) * 100
            vol_percent = max(0, min(100, vol_percent))
            set_volume(vol_percent)

    #  Display  
    text = f'Volume: {int(vol_percent)}%'
    position = (50, 100)
    font = cv2.FONT_HERSHEY_SCRIPT_COMPLEX
    font_scale = 3
    thickness = 3
    text_color = (255, 0, 255)
    bg_color = (0, 0, 0)  

    # size of textbox
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = position

    # rectangle  
    cv2.rectangle(img,
                  (x - 20, y - text_height - 20),
                  (x + text_width + 20, y + baseline + 20),
                  bg_color,
                  cv2.FILLED)

    # text
    cv2.putText(img, text, position, font, font_scale, text_color, thickness)

    # result
    cv2.imshow("Mac Volume Control", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
