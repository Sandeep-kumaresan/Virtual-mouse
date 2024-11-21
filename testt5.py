import cv2
import mediapipe as mp
import pyautogui
import time

def run_cam():
    pyautogui.FAILSAFE = True

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils

    plocX, plocY = 0, 0
    is_dragging = False
    has_clicked = False  # Track if click has been performed

    cap = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    screen_width, screen_height = pyautogui.size()
    prev_time = 0
    while True:
        success, img = cap.read()
        if not success:
            continue

        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        current_time = time.time()
        if current_time - prev_time > 1/30:  # Limit to 30 FPS
            prev_time = current_time

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = hand_landmarks.landmark

                    fingers_open = [False, False, False, False]
                    thumb_open = False

                    tip_ids = [
                        mp_hands.HandLandmark.THUMB_TIP,
                        mp_hands.HandLandmark.INDEX_FINGER_TIP,
                        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                        mp_hands.HandLandmark.RING_FINGER_TIP,
                        mp_hands.HandLandmark.PINKY_TIP,
                    ]
                    finger_tips = [landmarks[tip_id] for tip_id in tip_ids]

                    # Thumb
                    pseudo_fix_key = landmarks[2].x
                    if not (landmarks[3].x < pseudo_fix_key and landmarks[4].x < pseudo_fix_key):
                        thumb_open = True

                    # Index Finger
                    pseudo_fix_key = landmarks[6].y
                    if landmarks[7].y < pseudo_fix_key and landmarks[8].y < pseudo_fix_key:
                        fingers_open[0] = True

                    # Middle Finger
                    pseudo_fix_key = landmarks[10].y
                    if landmarks[11].y < pseudo_fix_key and landmarks[12].y < pseudo_fix_key:
                        fingers_open[1] = True

                    # Ring Finger
                    pseudo_fix_key = landmarks[14].y
                    if landmarks[15].y < pseudo_fix_key and landmarks[16].y < pseudo_fix_key:
                        fingers_open[2] = True

                    # Pinky
                    pseudo_fix_key = landmarks[18].y
                    if landmarks[19].y < pseudo_fix_key and landmarks[20].y < pseudo_fix_key:
                        fingers_open[3] = True

                    # Gesture recognition
                    if fingers_open == [True, True, True, True]:  # All fingers open: Left click
                        if is_dragging:
                            pyautogui.mouseUp()
                            is_dragging = False
                        if not has_clicked:
                            pyautogui.click()
                            has_clicked = True  # Set click state to prevent multiple clicks

                    elif fingers_open == [True, True, False, False]:  # V-shape: Cursor-moving state
                        if is_dragging:
                            pyautogui.mouseUp()
                            is_dragging = False
                        has_clicked = False  # Reset click state
                        x = int(finger_tips[1].x * screen_width)
                        y = int(finger_tips[1].y * screen_height)
                        pyautogui.moveTo(x, y)

                    elif fingers_open == [True, False, False, False] and not has_clicked:  # Right click
                        if is_dragging:
                            pyautogui.mouseUp()
                            is_dragging = False
                        pyautogui.rightClick()
                        has_clicked = True
                        

                    elif fingers_open == [False, True, True, True]:  # Scroll
                        scroll_y = landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].y * screen_height
                        if scroll_y > screen_height / 2:
                            pyautogui.scroll(-120)  # Scroll down
                        else:
                            pyautogui.scroll(120)  # Scroll up

                    elif fingers_open == [False, False, False, False]:  # Drag
                        if not is_dragging:
                            pyautogui.mouseDown()
                            is_dragging = True
                        x = int(finger_tips[1].x * screen_width)
                        y = int(finger_tips[1].y * screen_height)
                        pyautogui.moveTo(x, y)
                        has_clicked = False  # Reset click state

                    # Minimize window when fingers are close together
                    if thumb_open and all(fingers_open):
                        pyautogui.hotkey('alt', 'space', 'n')
                        time.sleep(0.5)

                    # Close window when only pinky finger is open
                    if fingers_open == [False, False, False, True]:
                        pyautogui.hotkey('alt', 'f4')
                        time.sleep(0.5)  # Adjust the duration of the delay as needed






                    # Draw hand landmarks and connections on the camera frame
                    mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Display camera output in the window
            cv2.imshow("Hand Tracking", img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# Start camera
run_cam()
