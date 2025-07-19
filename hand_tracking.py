import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Get screen resolution (useful for mapping)
screen_width, screen_height = pyautogui.size()
cap = cv2.VideoCapture(0)

# Set up hand module for 2 hands
with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as hands:

    click_states = [False, False]  # Debouncing for left/right click

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        frame_height, frame_width, _ = frame.shape

        black_screen = np.zeros((480, 640, 3), np.uint8)

        if results.multi_hand_landmarks:
            for h_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Draw hand landmarks on both original and black windows
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                mp_drawing.draw_landmarks(
                    black_screen, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
                )

                # -------- MOUSE Control Section (Example: right hand controls mouse) ----------
                # Dominant hand index finger tip controls the cursor
                if h_idx == 0:  # Use hand 0 as the mouse, hand 1 can be for scrolling
                    ix = int(hand_landmarks.landmark[8].x * frame_width)
                    iy = int(hand_landmarks.landmark[8].y * frame_height)
                    screen_x = int(hand_landmarks.landmark[8].x * screen_width)
                    screen_y = int(hand_landmarks.landmark[8].y * screen_height)
                    pyautogui.moveTo(screen_x, screen_y, duration=0.01)

                    # LEFT CLICK: Detect pinch (thumb tip close to index tip)
                    t_x = int(hand_landmarks.landmark[4].x * frame_width)
                    t_y = int(hand_landmarks.landmark[4].y * frame_height)
                    distance = math.hypot(ix - t_x, iy - t_y)
                    if distance < 40:
                        if not click_states[0]:
                            pyautogui.click()
                            click_states[0] = True
                    else:
                        click_states[0] = False

                # SECOND hand: different gesture for right-click or scroll
                if h_idx == 1:
                    # Example: Right click when thumb tip close to middle fingertip
                    mx = int(hand_landmarks.landmark[12].x * frame_width)
                    my = int(hand_landmarks.landmark[12].y * frame_height)
                    t2x = int(hand_landmarks.landmark[4].x * frame_width)
                    t2y = int(hand_landmarks.landmark[4].y * frame_height)
                    dist_r = math.hypot(mx - t2x, my - t2y)
                    if dist_r < 40:
                        if not click_states[1]:
                            pyautogui.rightClick()
                            click_states[1] = True
                    else:
                        click_states[1] = False

                    # Scroll with up/down movement of middle fingertip (very basic!)
                    prev_scroll_y = getattr(pyautogui, "_last_scroll_y", None)
                    curr_scroll_y = int(hand_landmarks.landmark[12].y * screen_height)
                    if prev_scroll_y is not None:
                        delta = curr_scroll_y - prev_scroll_y
                        if abs(delta) > 20:
                            pyautogui.scroll(-1 if delta > 0 else 1)
                    pyautogui._last_scroll_y = curr_scroll_y

        cv2.imshow('Hand Tracking', frame)
        cv2.imshow('Hands on Black', black_screen)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
