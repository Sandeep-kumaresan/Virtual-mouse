import cv2
import mediapipe as mp
import pyautogui
import time
import tkinter as tk
from tkinter import messagebox
from threading import Thread

class HandGestureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Recognition")
        self.root.geometry("400x300")

        self.start_button = tk.Button(self.root, text="Start Camera", command=self.start_camera)
        self.start_button.pack(pady=20)

        self.stop_button = tk.Button(self.root, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED)
        self.stop_button.pack(pady=20)

        self.gesture_label = tk.Label(self.root, text="No gesture detected", font=("Helvetica", 16))
        self.gesture_label.pack(pady=20)

        self.is_running = False
        self.thread = None

    def start_camera(self):
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.thread = Thread(target=self.run_cam)
            self.thread.start()

    def stop_camera(self):
        if self.is_running:
            self.is_running = False
            self.thread.join()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.gesture_label.config(text="No gesture detected")
            messagebox.showinfo("Info", "Camera stopped.")

    def run_cam(self):
        pyautogui.FAILSAFE = True

        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
        mp_draw = mp.solutions.drawing_utils

        plocX, plocY = 0, 0
        is_dragging = False
        has_clicked = False

        cap = cv2.VideoCapture(0)
        font = cv2.FONT_HERSHEY_SIMPLEX
        screen_width, screen_height = pyautogui.size()
        prev_time = 0

        while self.is_running:
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
                        gesture = "No gesture detected"
                        if fingers_open == [True, True, True, True]:  # All fingers open: Left click
                            gesture = "Left Click"
                            if is_dragging:
                                pyautogui.mouseUp()
                                is_dragging = False
                            if not has_clicked:
                                pyautogui.click()
                                has_clicked = True

                        elif fingers_open == [True, True, False, False]:  # V-shape: Cursor-moving state
                            gesture = "Move Cursor"
                            if is_dragging:
                                pyautogui.mouseUp()
                                is_dragging = False
                            has_clicked = False
                            x = int(finger_tips[1].x * screen_width)
                            y = int(finger_tips[1].y * screen_height)
                            pyautogui.moveTo(x, y)

                        elif fingers_open == [True, False, False, False] and not has_clicked:  # Right click
                            gesture = "Right Click"
                            if is_dragging:
                                pyautogui.mouseUp()
                                is_dragging = False
                            pyautogui.rightClick()
                            has_clicked = True

                        elif fingers_open == [False, True, True, True]:  # Scroll
                            gesture = "Scroll"
                            scroll_y = landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].y * screen_height
                            if scroll_y > screen_height / 2:
                                pyautogui.scroll(-120)  # Scroll down
                            else:
                                pyautogui.scroll(120)  # Scroll up

                        elif fingers_open == [False, False, False, False]:  # Drag
                            gesture = "Drag"
                            if not is_dragging:
                                pyautogui.mouseDown()
                                is_dragging = True
                            x = int(finger_tips[1].x * screen_width)
                            y = int(finger_tips[1].y * screen_height)
                            pyautogui.moveTo(x, y)
                            has_clicked = False

                        # Minimize window when fingers are close together
                        if thumb_open and all(fingers_open):
                            gesture = "Minimize Window"
                            pyautogui.hotkey('alt', 'space', 'n')
                            time.sleep(0.5)

                        # Close window when only pinky finger is open
                        if fingers_open == [False, False, False, True]:
                            gesture = "Close Window"
                            pyautogui.hotkey('alt', 'f4')
                            time.sleep(0.5)

                        # Update gesture label
                        self.update_gesture_label(gesture)

                        # Draw hand landmarks and connections on the camera frame
                        mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Display camera output in the window
                cv2.imshow("Hand Tracking", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

    def update_gesture_label(self, gesture):
        self.gesture_label.config(text=f"Gesture: {gesture}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HandGestureApp(root)
    root.mainloop()
