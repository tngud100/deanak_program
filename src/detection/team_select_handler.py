from src.utils.error_handler import NoDetectionError, ErrorHandler
from src.models.screen_state import ScreenState
from src import state
import random
import time

class TeamSelectHandler:
    def __init__(self, input_controller, image_matcher, capture, MAX_DETECTION_ATTEMPTS=3):
        self.image_matcher = image_matcher
        self.input_controller = input_controller
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.x_range = [1000, 1500]
        self.y_range = [400, 850]

    def handle_team_select_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        """팀 선택 화면을 처리합니다.
        
        Args:
            screen: 현재 화면 이미지
            loaded_templates: 로드된 템플릿 이미지들
            screen_state: 화면 상태 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            if not screen_state.team_select_passed and screen_state.notice_passed:
                if screen_state.get_count("team_select") > self.MAX_DETECTION_ATTEMPTS:
                    raise NoDetectionError(f"team_select_screen 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")
                
                # 팀 선택 화면 탐지
                # top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['team_select_screen'], threshold=0.8)
                # if top_left and bottom_right:
                    # 팀 선택 텍스트 탐지
                top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['team_select_icon'], threshold=0.8, template_key = "team_select_icon")
                
                if top_left and bottom_right:
                    # box_height = bottom_right[1] - top_left[1]
                    # offset_y = top_left[1] + box_height * 10
                    
                    # self.input_controller.click(random.randint(top_left[0], bottom_right[0] - 10), offset_y)
                    time.sleep(2.5)
                    random_x = random.randint(self.x_range[0], self.x_range[1])
                    random_y = random.randint(self.y_range[0], self.y_range[1])
                    self.input_controller.click(random_x, random_y, 1)
                    screen_state.team_select_passed = True
                    print("팀 선택 완료")
                    # time.sleep(2)
                    return True
            
            return False

        except NoDetectionError as e:
            self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_TEAM_SELECT_SCENE)
            raise e