from src.detection.duplicate_login_handler import DuplicateLoginHandler
from src.utils.error_handler import DuplicateLoginError, NoDetectionError, ErrorHandler
from src.models.screen_state import ScreenState
from src import state
import time

class NoticeHandler:
    def __init__(self, input_controller, image_matcher, capture, MAX_DETECTION_ATTEMPTS=12):
        self.image_matcher = image_matcher
        self.input_controller = input_controller
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.duplicate_login_handler = DuplicateLoginHandler(self.image_matcher, self.capture)

    def handle_notice_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        """공지사항 화면을 처리합니다.
        
        Args:
            screen: 현재 화면 이미지
            loaded_templates: 로드된 템플릿 이미지들
            screen_state: 화면 상태 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            if not screen_state.notice_passed and screen_state.password_passed:
                if screen_state.get_count("notice") > self.MAX_DETECTION_ATTEMPTS:
                    raise NoDetectionError(f"noticeScreen 화면 스킵과정에서 team_select_screen을 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")
                
                if self.image_matcher.process_template(screen, 'notice', loaded_templates):
                    time.sleep(0.5)
                    self.input_controller.press_key("esc")
                    screen_state.notice_passed = True
                    print("공지사항 확인 완료")
                    return True
            
            return False

        except NoDetectionError as e:
            try:
                self.duplicate_login_handler.check_duplicate_login(screen, loaded_templates, deanak_id)
            except DuplicateLoginError as e:
                print("사용자가 중복으로 로그인하여 있습니다.")
                raise e
            else:
                self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_NOTICE_SCENE)
                raise e

            # self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_NOTICE_SCENE)
            # raise e

        # except DuplicateLoginError as e:
        #     raise e