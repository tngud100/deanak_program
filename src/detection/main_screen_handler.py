import random
from cv2 import threshold
from src.utils import input_controller
from src.utils.error_handler import NoDetectionError, NoDetectionPCIconError, ErrorHandler
from src.models.screen_state import ScreenState
from src import state
import time

class MainScreenHandler:
    def __init__(self, input_controller, image_matcher, capture, MAX_DETECTION_ATTEMPTS=5, MAX_PCICON_DETECTION_ATTEMPTS=3):
        self.image_matcher = image_matcher
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.MAX_PCICON_DETECTION_ATTEMPTS = MAX_PCICON_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.input_controller = input_controller
        self.x_range = [690, 800]
        self.y_range = [995, 1015]

    def handle_main_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        """메인 화면을 처리합니다.
        Args:
            screen: 현재 화면 이미지
            loaded_templates: 로드된 템플릿 이미지들
            screen_state: 화면 상태 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            if not screen_state.main_screen_passed and screen_state.purchase_screen_passed:
                
                # if not screen_state.pc_icon_passed:
                #     screen_state.increment_count("pc_icon")
                #     if screen_state.get_count("pc_icon") > self.MAX_PCICON_DETECTION_ATTEMPTS:
                #         raise NoDetectionPCIconError(f"pc_bar 화면이 {self.MAX_PCICON_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")

                #     top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['pc_icon_bar'], threshold=0.6)
                #     if top_left is None or bottom_right is None:
                #         return False
                #     roi = (top_left[0], top_left[1] - 52, bottom_right[0], top_left[1])
                #     if self.image_matcher.process_template(screen, 'pc_icon', loaded_templates, threshold=0.7, roi=roi):
                #         screen_state.pc_icon_passed = True
                #         print("pc_icon 확인 완료")
                #         return True

                #     return False

                if screen_state.get_count("main_screen") > self.MAX_DETECTION_ATTEMPTS:
                    raise NoDetectionError(f"main_screen 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")

                top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['main_screen'])
                if top_left and bottom_right:
                    # roi = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                    # if self.image_matcher.process_template(screen, 'market_btn', loaded_templates, click=True, roi=roi):
                    random_x = random.randint(self.x_range[0], self.x_range[1])
                    random_y = random.randint(self.y_range[0], self.y_range[1])
                    self.input_controller.click(random_x, random_y, 1)
                    screen_state.main_screen_passed = True
                    print("메인 화면 처리 완료")
                    time.sleep(1)
                    return True
            
            return False

        except NoDetectionError as e:
            self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_MAIN_SCREEN_SCENE)
            raise e
        except NoDetectionPCIconError as e:
            self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_PC_ICON)
            raise e