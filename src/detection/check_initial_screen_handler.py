import random

from cv2 import threshold
from pyautogui import click
from src.utils import input_controller
from src.utils.api import Api
from src.utils.error_handler import NoDetectionError, ErrorHandler
from src import state
import asyncio

class CheckInitialScreenHandler:
    def __init__(self, input_controller, image_matcher, template_service, capture, MAX_DETECTION_ATTEMPTS=25):
        self.image_matcher = image_matcher
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.api = Api()
        self.input_controller = input_controller
        self.template_service = template_service
        self.detect_attempt = 0
        self.clicked_naver_login = False

    async def detect_screen(self, screen, loaded_templates):
        in_game_top_left, in_game_bottom_right, _ = self.image_matcher.detect_template(
            screen, 
            loaded_templates['password_screen']
        )
        
        otp_top_left, otp_bottom_right, _ = self.image_matcher.detect_template(
            screen,
            loaded_templates['otp_frame'],
            threshold=0.6
        )
        
        if self.image_matcher.process_template(screen, "connect_logged_in_id_error", loaded_templates, threshold=0.6):
            self.input_controller.hotkey('Enter')
            await asyncio.sleep(1.5)
            await self.api.send_game_start(self.state.worker_id)

        
        return (in_game_top_left, in_game_bottom_right), (otp_top_left, otp_bottom_right)

    async def handle_initial_screen_check(self, deanak_info):
        """OTP 혹은 게임시작 화면을 감지 후 서비스 처리 함수 호출.
        Args:
            deanak_info: 대낙 정보가 담긴 리스트
        Returns:
            bool: 처리 성공 여부
        """
        try:
            loaded_templates = self.template_service.get_templates()
            self.detect_attempt = 0
            self.clicked_naver_login = False

            async def detection_task():
                while True:
                    if self.detect_attempt > self.MAX_DETECTION_ATTEMPTS:
                        raise NoDetectionError(f"초기 화면을 탐지하지 못했습니다")

                    screen = self.capture.screen_capture()
                    print(f"초기 화면을 감지하는 중 ...{self.detect_attempt}/{self.MAX_DETECTION_ATTEMPTS}")
                    if deanak_info["login_type"] == "네이버" and not self.clicked_naver_login:
                        print("네이버 로그인체크")
                        if self.image_matcher.process_template(screen, "naver_login", loaded_templates, click=True, threshold=0.8):
                            self.clicked_naver_login = True
                            await asyncio.sleep(1)
                            await self.api.send_naver_login(deanak_info["worker_id"])
                            continue
                        if self.image_matcher.process_template(screen, "naver_login_grey", loaded_templates, click=True, threshold=0.8):
                            self.clicked_naver_login = True
                            await asyncio.sleep(1)
                            await self.api.send_naver_login(deanak_info["worker_id"])
                            continue
                        
                        await asyncio.sleep(3)
                    
                    self.input_controller.hotkey('Ctrl')
                    
                    (in_game_top_left, in_game_bottom_right), (otp_top_left, otp_bottom_right) = await self.detect_screen(screen, loaded_templates)

                    if in_game_top_left and in_game_bottom_right:
                        print("패스워드 화면 감지 완료")
                        return_dict = deanak_info.copy()
                        return_dict["otp"] = 0
                        return return_dict

                    if otp_top_left and otp_bottom_right:
                        print("OTP화면 감지 완료")
                        return_dict = deanak_info.copy()
                        return_dict["otp"] = 1
                        return return_dict
                        
                    self.detect_attempt += 1
                    await asyncio.sleep(2)

            return await detection_task()
                
        except NoDetectionError as e:
            raise e