import pyautogui
from PIL import Image
import os
import cv2
import numpy as np

class CaptureUtil:
    def screen_capture(self, region=None):
        """화면을 캡처하여 흑백 이미지로 반환합니다."""
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # PIL -> OpenCV 색상 공간 변환
        return frame