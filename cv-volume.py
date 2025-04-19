import cv2
import mediapipe as mp
import math
import os
import time
import pygame
import random
from datetime import datetime
from collections import deque

# setup 
pygame.mixer.init()
click_sound = pygame.mixer.Sound("click.mp3")
click_sound.set_volume(0.5)

mute_img = cv2.imread("mute.png", cv2.IMREAD_UNCHANGED)
unmute_img = cv2.imread("unmute.png", cv2.IMREAD_UNCHANGED)
overlay_img = None
overlay_start_time = None
overlay_duration = 1.5

volume_history = deque(maxlen=100)
start_time = time.time()

def set_volume(volume_percent):
    volume_percent = max(0, min(100, int(volume_percent)))
    os.system(f"osascript -e 'set volume output volume {volume_percent}'")

def overlay_fade_center(img, overlay, alpha):
    if overlay is None or overlay.shape[2] != 4:
        return
    oh, ow = overlay.shape[:2]
    scale = 1.5
    oh, ow = int(oh * scale), int(ow * scale)
    overlay = cv2.resize(overlay, (ow, oh), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    x, y = (w - ow) // 2, (h - oh) // 2
    overlay_rgb = overlay[:, :, :3]
    overlay_alpha = overlay[:, :, 3] / 255.0 * alpha
    for c in range(3):
        img[y:y+oh, x:x+ow, c] = (
            overlay_alpha * overlay_rgb[:, :, c] +
            (1 - overlay_alpha) * img[y:y+oh, x:x+ow, c]
        ).astype("uint8")

def is_peace(lm):
    return (lm[8].y < lm[6].y and lm[12].y < lm[10].y and
            lm[16].y > lm[14].y and lm[20].y > lm[18].y)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
min_distance = 20
max_distance = 450
status_text = ""
peace_active = False
is_muted = False
last_volume = 50

# tips
tips = [
    "Listening to music too loud can cause hearing loss.",
    "Take regular breaks from headphones.",
    "Safe volume is around 60% or lower.",
    "Protect your ears, especially in noisy environments.",
    "Use noise-cancelling to reduce volume strain.",
    "Even short bursts of loud music can damage hearing.",
    "Keep your ears safe for the future.",
]
tip_font = cv2.FONT_HERSHEY_SIMPLEX
tip_font_scale = 1.5
tip_thickness = 2
tip_color = (200, 200, 200)
tip_y = None
tip_speed = 4
tip_spacing = 100
tip_queue = [random.choice(tips)]
tip_positions = [1280]

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    h, w, _ = img.shape
    if tip_y is None:
        tip_y = h - 30

    peace_detected_now = False

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            lmList = handLms.landmark

            if is_peace(lmList):
                peace_detected_now = True
                if not peace_active:
                    click_sound.play()
                    time.sleep(0.3)
                    if not is_muted:
                        last_volume = last_volume if last_volume > 0 else 50
                        set_volume(0)
                        is_muted = True
                        status_text = "- MUTED -"
                        overlay_img = mute_img
                        overlay_start_time = time.time()
                    else:
                        set_volume(last_volume)
                        is_muted = False
                        click_sound.play()
                        status_text = f"Volume: {int(last_volume)}%"
                        overlay_img = unmute_img
                        overlay_start_time = time.time()
                    peace_active = True
            elif not is_muted:
                x1, y1 = int(lmList[4].x * w), int(lmList[4].y * h)
                x2, y2 = int(lmList[8].x * w), int(lmList[8].y * h)
                length = math.hypot(x2 - x1, y2 - y1)
                volume = (length - min_distance) / (max_distance - min_distance) * 100
                volume = max(0, min(100, volume))
                last_volume = volume
                set_volume(volume)
                status_text = f"Volume: {int(volume)}%"

    if not peace_detected_now:
        peace_active = False

    # clock and how long it's running
    current_time = datetime.now().strftime("%H:%M:%S")
    session_duration = int(time.time() - start_time)
    minutes, seconds = divmod(session_duration, 60)
    duration_text = f"Listening: {minutes:02}:{seconds:02}"

    clock_font = cv2.FONT_HERSHEY_SIMPLEX
    clock_scale = 1.4
    clock_color = (220, 200, 180)
    clock_thickness = 2
    padding = 20

    clock_text_size = cv2.getTextSize(current_time, clock_font, clock_scale, clock_thickness)[0]
    duration_text_size = cv2.getTextSize(duration_text, clock_font, clock_scale, clock_thickness)[0]

    x_clock = w - clock_text_size[0] - padding
    x_duration = w - duration_text_size[0] - padding

    cv2.putText(img, current_time, (x_clock, 50), clock_font, clock_scale, clock_color, clock_thickness)
    cv2.putText(img, duration_text, (x_duration, 90), clock_font, clock_scale, clock_color, clock_thickness)

    # volume text in the middle
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2.8
    thickness = 5
    status_color = (0, 0, 255) if is_muted else (240, 230, 200)
    bg_color = (0, 0, 0)
    (tw, th), baseline = cv2.getTextSize(status_text, font, font_scale, thickness)
    center_x = (w - tw) // 2
    high_y = int(h * 0.10)
    cv2.rectangle(img, (center_x - 40, high_y - th - 40),
                  (center_x + tw + 40, high_y + baseline + 40),
                  bg_color, cv2.FILLED)
    cv2.putText(img, status_text, (center_x, high_y),
                font, font_scale, status_color, thickness)

    # small volume bar below text
    if not is_muted:
        bar_x = center_x
        bar_y = high_y + baseline + 60
        bar_width = int(tw * (last_volume / 100))
        bar_height = 10
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (139, 0, 139), cv2.FILLED)

    # graph on the top left
    volume_history.append(last_volume if not is_muted else 0)
    graph_x, graph_y = 20, 20
    graph_w, graph_h = 400, 140
    title_gap = 80
    cv2.putText(img, "VOLUME HISTORY", (graph_x + 10, graph_y + 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 2)
    for i in range(1, len(volume_history)):
        x1 = graph_x + int((i - 1) / 100 * graph_w)
        y1 = graph_y + title_gap + graph_h - int(volume_history[i - 1] / 100 * graph_h)
        x2 = graph_x + int(i / 100 * graph_w)
        y2 = graph_y + title_gap + graph_h - int(volume_history[i] / 100 * graph_h)
        cv2.line(img, (x1, y1), (x2, y2), (200, 100, 255), 2)

    # tips scrolling at the bottom
    cv2.rectangle(img, (0, h - 80), (w, h), (0, 0, 0), cv2.FILLED)
    for i in range(len(tip_queue)):
        tip_text = tip_queue[i]
        x_pos = tip_positions[i]
        cv2.putText(img, tip_text, (x_pos, tip_y),
                    tip_font, tip_font_scale, tip_color, tip_thickness)
        tip_positions[i] -= tip_speed

    while tip_positions and tip_positions[0] < -1000:
        tip_queue.pop(0)
        tip_positions.pop(0)

    if not tip_positions or (
        tip_positions[-1] +
        cv2.getTextSize(tip_queue[-1], tip_font, tip_font_scale, tip_thickness)[0][0] + tip_spacing < w
    ):
        new_tip = random.choice(tips)
        tip_queue.append(new_tip)
        tip_positions.append(w + 50)

    # show image quickly when muted/unmuted
    if overlay_img is not None:
        elapsed = time.time() - overlay_start_time
        if elapsed < overlay_duration:
            alpha = 1 - (elapsed / overlay_duration)
            overlay_fade_center(img, overlay_img, alpha)
        else:
            overlay_img = None

    cv2.imshow("Smart Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
