import random
from src.utils.error_handler import NoDetectionError, ErrorHandler
from src.models.screen_state import ScreenState
from src import state
import time

class GetAllScreenHandler:
    def __init__(self, input_controller, image_matcher, capture, MAX_DETECTION_ATTEMPTS=3):
        self.image_matcher = image_matcher
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.input_controller = input_controller
        self.arrange_x_range = [835, 884]
        self.arrange_y_range = [244, 251]
        self.get_all_x_range = [1216, 1376]
        self.get_all_y_range = [866, 886]

    def handle_get_all_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        """모두 받기 화면을 처리합니다.
        Args:
            screen: 현재 화면 이미지
            loaded_templates: 로드된 템플릿 이미지들
            screen_state: 화면 상태 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            if screen_state.get_item_screen_passed and not screen_state.get_all_btn_screen_passed:
                screen_state.increment_count("arrange_btn")
                if screen_state.get_count("arrange_btn") > self.MAX_DETECTION_ATTEMPTS:
                    raise NoDetectionError(f"arrange_btn_screen 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")
                
                if not screen_state.arrange_btn_screen_passed:
                    top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['arrange_btn_screen'], template_key = 'arrange_btn_screen')
                    if top_left and bottom_right:
                        # roi = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                        # if self.image_matcher.process_template(screen, 'arrange_btn', loaded_templates, click=True, roi=roi):
                        random_x = random.randint(self.arrange_x_range[0], self.arrange_x_range[1])
                        random_y = random.randint(self.arrange_y_range[0], self.arrange_y_range[1])
                        self.input_controller.click(random_x, random_y, 1)
                        screen_state.arrange_btn_screen_passed = True
                        time.sleep(1)
                        print("정렬 버튼 클릭 완료")

                if not screen_state.get_all_btn_screen_passed and screen_state.arrange_btn_screen_passed:
                    screen_state.increment_count("get_all_btn")
                    if screen_state.get_count("get_all_btn") > self.MAX_DETECTION_ATTEMPTS:
                        raise NoDetectionError(f"get_all_btn_screen 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")

                    top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['get_all_btn_screen'], template_key = 'get_all_btn_screen')
                    if top_left and bottom_right:
                        # roi = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                        # if self.image_matcher.process_template(screen, 'get_all_btn', loaded_templates, click=True, roi=roi):
                        random_x = random.randint(self.get_all_x_range[0], self.get_all_x_range[1])
                        random_y = random.randint(self.get_all_y_range[0], self.get_all_y_range[1])
                        self.input_controller.click(random_x, random_y, 1)
                        screen_state.get_all_btn_screen_passed = True
                        print("모두 받기 처리 완료")
                        time.sleep(1)
                        return True
            
            return False

        except NoDetectionError as e:
            self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_GET_ALL_SCREEN_SCENE)
            raise e