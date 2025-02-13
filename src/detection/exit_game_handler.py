import random
from src.utils.error_handler import ErrorHandler, NoDetectionError
from src.models.screen_state import ScreenState
from src import state
import time

class ExitGameHandler:
    def __init__(self, input_controller, image_matcher, capture, MAX_DETECTION_ATTEMPTS=5):
        self.image_matcher = image_matcher
        self.capture = capture
        self.MAX_DETECTION_ATTEMPTS = MAX_DETECTION_ATTEMPTS
        self.state = state
        self.error_handler = ErrorHandler()
        self.input_controller = input_controller
    
    def _handle_screen_detection(self, screen, screen_state, screen_type, required_previous_state, loaded_templates, x_range, y_range):
        if required_previous_state is not None and not required_previous_state:
            return False
            
        if getattr(screen_state, f"{screen_type}_screen_passed"):
            return True
        
        screen = self.capture.screen_capture()

        screen_state.increment_count(screen_type)
        if screen_state.get_count(screen_type) > self.MAX_DETECTION_ATTEMPTS:
            raise NoDetectionError(f"{screen_type} 화면이 {self.MAX_DETECTION_ATTEMPTS}회 이상 탐지되지 않았습니다.")
        
        top_left, bottom_right, _ = self.image_matcher.detect_template(screen, loaded_templates[screen_type], threshold=0.6)
        if top_left and bottom_right:
            # roi = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
            # if self.image_matcher.process_template(screen, f"{screen_type}_btn", loaded_templates, click=True, roi=roi, threshold=0.6):
            random_x = random.randint(x_range[0], x_range[1])
            random_y = random.randint(y_range[0], y_range[1])
            self.input_controller.click(random_x, random_y, 1)
            setattr(screen_state, f"{screen_type}_screen_passed", True)
            time.sleep(2)
            return True

        return False

    def handle_exit_game_screen(self, screen, loaded_templates, screen_state: ScreenState, deanak_id):
        try:
            
            self._handle_screen_detection(
                screen, screen_state, "exit_get_item",
                required_previous_state=None,
                loaded_templates=loaded_templates,
                x_range=[1582, 1623],
                y_range=[80, 116]
            )

            self._handle_screen_detection(
                screen, screen_state, "exit_main",
                required_previous_state=screen_state.exit_get_item_screen_passed,
                loaded_templates=loaded_templates,
                x_range=[1582, 1623],
                y_range=[80, 116]
            )

            self._handle_screen_detection(
                screen, screen_state, "exit_team",
                required_previous_state=screen_state.exit_main_screen_passed,
                loaded_templates=loaded_templates,
                x_range=[1583, 1620],
                y_range=[121, 153]
            )

            self._handle_screen_detection(
                screen, screen_state, "exit_modal",
                required_previous_state=screen_state.exit_team_screen_passed,
                loaded_templates=loaded_templates,
                x_range=[758, 938],
                y_range=[614, 637]
            )
            time.sleep(1)

        except NoDetectionError as e:
            self.error_handler.handle_error(e, {"deanak_id" : deanak_id}, user_message=self.error_handler.NO_DETECT_EXIT_GAME_SCREEN_SCENE)
            raise e