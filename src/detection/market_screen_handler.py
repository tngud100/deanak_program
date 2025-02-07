from cv2 import threshold
from src.utils.error_handler import NoDetectionError, ErrorHandler
from src.models.screen_state import ScreenState
from src import state
import time


class MarketScreenHandler:
    def __init__(self, image_matcher, capture, MAX_DETECTION_ATTEMPTS=12):
        self.image_matcher = image_matcher
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()

    def handle_market_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        """마켓 화면을 처리합니다.
        Args:
            screen: 현재 화면 이미지
            loaded_templates: 로드된 템플릿 이미지들
            screen_state: 화면 상태 객체
            
        Returns:
            bool: 처리 성공 여부
        """
        try:
            if not screen_state.market_screen_passed and screen_state.main_screen_passed:
                if screen_state.get_count("market_screen") > self.MAX_DETECTION_ATTEMPTS:
                    raise NoDetectionError(f"market_screen 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")
                
                top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates['market_screen'], threshold=0.95)
                print(f"감지 완료: screen_type: market_screen, top_left: {top_left}, bottom_right: {bottom_right}")
                if top_left and bottom_right:
                    roi = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                    if self.image_matcher.process_template(screen, 'list_btn', loaded_templates, click=True, roi=roi, threshold=0.8):
                        screen_state.market_screen_passed = True
                        print("마켓 화면 처리 완료")
                        time.sleep(1)
                        return True
        
            return False

        except NoDetectionError as e:
            self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_MARKET_SCREEN_SCENE)
            raise e