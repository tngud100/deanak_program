import random
from cv2 import threshold
from src.detection.duplicate_login_handler import DuplicateLoginHandler
from src.utils.error_handler import DuplicateLoginError, NoDetectionError, ErrorHandler
from src.models.screen_state import ScreenState
from src import state
import time

class AnyKeyScreenHandler:
    def __init__(self, input_controller, image_matcher, capture, MAX_DETECTION_ATTEMPTS=25):
        self.image_matcher = image_matcher
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.input_controller = input_controller
        self.duplicate_login_handler = DuplicateLoginHandler(self.image_matcher, self.capture)

    def handle_anykey_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        """마켓 화면을 처리합니다.
        Args:
            screen: 현재 화면 이미지
            loaded_templates: 로드된 템플릿 이미지들
            screen_state: 화면 상태 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            if not screen_state.anykey_passed:
                if screen_state.get_count("anykey") > self.MAX_DETECTION_ATTEMPTS:
                    raise NoDetectionError(f"anykey 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")
                
                top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['anykey_screen'], threshold=0.6)
                print(f"감지 완료: screen_type: anykey, top_left: {top_left}, bottom_right: {bottom_right}")
                
                if top_left and bottom_right:
                    time.sleep(0.5)
                    self.input_controller.hotkey("ctrl")
                    screen_state.anykey_passed = True
                    print("anykey 화면 처리 완료")
                    time.sleep(1)
                    return True
        
            return False

        except NoDetectionError as e:
            try:
                self.duplicate_login_handler.check_duplicate_login(screen, loaded_templates, deanak_id)
            except DuplicateLoginError as e:
                print("사용자가 중복으로 로그인하여 있습니다.")
                raise e
            else:
                self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_ANYKEY_SCENE)
                raise e