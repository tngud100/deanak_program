import cv2
import numpy as np
import easyocr
import random
from src.utils.error_handler import ErrorHandler
from src.utils.input_controller import InputController

class ImageMatcher:
    def __init__(self, input_controller: InputController):
        self.error_handler = ErrorHandler()
        self.reader = easyocr.Reader(['en','ko'])  # OCR 리더 초기화
        self.input_controller = input_controller

    def detect_template(self, screen, templates, threshold=0.6, roi=None):
        """이미지에서 템플릿 위치 탐지
        
        Args:
            screen: 검색할 스크린샷 이미지
            template: 찾을 템플릿 이미지
            threshold: 매칭 임계값 (기본값: 0.6)
            
        Returns:
            tuple: (top_left, bottom_right, max_val) - 템플릿이 발견된 위치와 매칭 점수
        """
        # templates가 단일 이미지인 경우 리스트로 변환
        if not isinstance(templates, list):
            templates = [templates]

        # ROI가 설정된 경우, 해당 영역만 추출
        original_screen = screen.copy()
        if roi is not None:
            x1, y1, x2, y2 = roi
            screen = original_screen[y1:y2, x1:x2]  # height(y), width(x) 순서로 슬라이싱
            # print(f"ROI 적용: ({x1}, {y1}, {x2}, {y2})")
            # print(f"잘린 이미지 크기: {screen.shape}")
        
        found = None
        
        # 템플릿 리스트를 순차적으로 탐지 시도
        for template in templates:
            template_height, template_width = template.shape[:2]
            found = None

            # 템플릿이 ROI보다 큰 경우 스킵
            if roi is not None and (template_height > screen.shape[0] or template_width > screen.shape[1]):
                print(f"[DEBUG] 템플릿 크기({template_width}x{template_height})가 ROI 크기({screen.shape[1]}x{screen.shape[0]})보다 큼 - 스킵")
                continue

            # 다중 스케일 템플릿 매칭을 위한 루프
            for scale in np.linspace(0.8, 1.0, 10)[::-1]:
                resized_template_width = int(template_width * scale)
                resized_template_height = int(template_height * scale)

                # 리사이즈된 템플릿이 ROI보다 큰 경우 스킵
                if roi is not None and (resized_template_height > screen.shape[0] or resized_template_width > screen.shape[1]):
                    continue

                resized = cv2.resize(template, (resized_template_width, resized_template_height))
                result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                if max_val >= threshold:
                    if found is None or max_val > found[0]:
                        found = (max_val, max_loc, scale)
                        print(f"[found] 매칭률:{max_val}, x좌표:({max_loc[0]}), y좌표:({max_loc[1]})")

            # 템플릿 위치 반환 (탐지에 성공한 경우)
            if found:
                max_val, max_loc, scale = found
                start_x = int(max_loc[0])
                start_y = int(max_loc[1])
                end_x = start_x + int(template_width * scale)
                end_y = start_y + int(template_height * scale)

                # ROI가 설정된 경우, 전체 화면의 좌표로 변환
                if roi is not None:
                    start_x += x1
                    start_y += y1
                    end_x += x1
                    end_y += y1

                print(f"매칭률:{max_val}, x좌표:({start_x},{end_x}), y좌표:({start_y},{end_y})")
                return (start_x, start_y), (end_x, end_y), max_val

        # 모든 템플릿을 탐지했으나 성공하지 못한 경우
        return None, None, None

    def process_template(self, screen, template_key, templates, click=False, roi=None, _range=10, threshold=0.6):
        """템플릿을 감지하고 필요한 경우 클릭 수행
        
        Args:
            screen: 검색할 스크린샷 이미지
            template_key: 템플릿 키
            templates: 템플릿 딕셔너리
            click: 클릭 여부
            roi: 관심 영역 (x1, y1, x2, y2)
            
        Returns:
            bool: 감지 성공 여부
        """
        if template_key not in templates:
            print(f"템플릿 \"{template_key}\" 찾기 실패")
            return False
        
        top_left, bottom_right, _ = self.detect_template(screen, templates[template_key], roi=roi, threshold=threshold)
        if top_left and bottom_right:
            # print(f"템플릿 \"{template_key}\" 감지 성공")
            if click:
                # 여백을 10픽셀 주고 랜덤한 좌표 선택
                random_x = random.randint(top_left[0] + _range, bottom_right[0] - _range)
                random_y = random.randint(top_left[1] + _range, bottom_right[1] - _range)
                self.input_controller.click(random_x, random_y)
            print(f"템플릿 '{template_key} : {top_left} ~ {bottom_right}' 감지 성공")
            return True
        return False

    async def extract_text(self, screen, template, threshold=0.8, roi=None):
        """이미지에서 텍스트 추출
        
        Args:
            screen: 검색할 스크린샷 이미지
            template: 텍스트 영역 템플릿
            threshold: 매칭 임계값 (기본값: 0.8)
            roi: 관심 영역 (x1, y1, x2, y2)
            
        Returns:
            str: 추출된 텍스트
        """
        if roi:
            x1, y1, x2, y2 = roi
            screen = screen[y1:y2, x1:x2].copy()

        # 텍스트 영역 찾기
        top_left, bottom_right, max_val = self.detect_template(screen, template, threshold)
        if not top_left or not bottom_right:
            return None

        # 텍스트 영역 추출
        x1, y1 = top_left
        x2, y2 = bottom_right
        text_roi = screen[y1:y2, x1:x2]

        # OCR 수행
        results = self.reader.readtext(text_roi)
        if results:
            text = ''.join([result[1] for result in results])
            return text
        return None