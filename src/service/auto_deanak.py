from src.utils.error_handler import DuplicateLoginError, NoDetectionError, DeanakError, WrongPasswordError, APICallError, TemplateEmptyError
from src.utils.image_matcher import ImageMatcher
from src.utils.input_controller import InputController
from src.utils.remote_controller import RemoteController
from src.service.template_service import TemplateService
from src.utils.capture import CaptureUtil
from src.utils.error_handler import ErrorHandler
from src.models.screen_state import ScreenState
from src import state
from database import get_db_context
from src.dao.remote_pcs_dao import RemoteDao
from src.utils.api import Api

from src.detection.password_handler import PasswordHandler
from src.detection.notice_handler import NoticeHandler
from src.detection.team_select_handler import TeamSelectHandler
from src.detection.purchase_screen_handler import PurchaseScreenHandler
from src.detection.main_screen_handler import MainScreenHandler
from src.detection.market_screen_handler import MarketScreenHandler
from src.detection.get_item_screen_handler import GetItemScreenHandler
from src.detection.get_all_screen_handler import GetAllScreenHandler
from src.detection.top_class_screen_handler import TopClassScreenHandler
from src.detection.duplicate_login_handler import DuplicateLoginHandler
import asyncio

class AutoDeanak:
    def __init__(self, image_matcher: ImageMatcher, input_controller: InputController, remote: RemoteController, template_service: TemplateService, capture: CaptureUtil, state: state, remote_pcs_dao: RemoteDao):
        self.image_matcher = image_matcher
        self.input_controller = input_controller
        self.remote = remote
        self.template_service = template_service
        self.capture = capture
        self.error_handler = ErrorHandler()
        self.state = state
        self.MAX_DETECTION_ATTEMPTS = 5
        self.screen_state = ScreenState()
        self.remote_pcs_dao = remote_pcs_dao
        self.api = Api()

        # 핸들러 초기화
        self.password_handler = PasswordHandler(self.image_matcher, self.input_controller, self.capture)
        self.notice_handler = NoticeHandler(self.image_matcher, self.input_controller, self.capture)
        self.team_select_handler = TeamSelectHandler(self.image_matcher, self.input_controller, self.capture, self.MAX_DETECTION_ATTEMPTS)
        self.purchase_screen_handler = PurchaseScreenHandler(self.image_matcher, self.input_controller, self.capture)
        self.main_screen_handler = MainScreenHandler(self.image_matcher, self.input_controller, self.capture, self.MAX_DETECTION_ATTEMPTS)
        self.market_screen_handler = MarketScreenHandler(self.image_matcher, self.input_controller, self.capture, self.MAX_DETECTION_ATTEMPTS)
        self.get_item_screen_handler = GetItemScreenHandler(self.image_matcher, self.input_controller, self.capture, self.MAX_DETECTION_ATTEMPTS)
        self.get_all_screen_handler = GetAllScreenHandler(self.image_matcher, self.input_controller, self.capture, self.MAX_DETECTION_ATTEMPTS)
        self.top_class_screen_handler = TopClassScreenHandler(self.image_matcher, self.input_controller, self.capture)
        self.duplicate_login_handler = DuplicateLoginHandler(self.image_matcher, self.input_controller, self.capture)

    async def _getter_info(self, deanak_info):
        worker_id = deanak_info['worker_id']
        deanak_id = deanak_info['deanak_id']
        password_list = list(str(deanak_info['pw2']))
        server_id = await self.state.unique_id().read_unique_id()

        if not server_id or not worker_id or not deanak_id or not password_list:
            raise ValueError("deanak_info의 파라미터를 확인해주세요.")

        return worker_id, password_list, server_id, deanak_id

    async def deanak_start(self, deanak_info:dict=None):
        """대낙 프로세스 시작"""
        try:
            print("대낙 시작")
            if not deanak_info:
                raise ValueError("대낙 정보가 없습니다.")
            
            worker_id, password_list, server_id, deanak_id = await self._getter_info(deanak_info)
            print(worker_id, password_list)
            
            loaded_templates = self.template_service.get_templates(password_list)
            
            self.screen_state.reset_all()  # 상태 초기화
            
            self.state.is_running = True
            while self.state.is_running:
                try:
                    screen = self.capture.screen_capture()
                    print("capturing...")

                    self.duplicate_login_handler.check_duplicate_login(screen, loaded_templates, deanak_id)
                    
                    if not self.screen_state.password_passed:
                        self.screen_state.increment_count("password")
                    if not self.screen_state.notice_passed and self.screen_state.password_passed:
                        self.screen_state.increment_count("notice")
                    if not self.screen_state.team_select_passed and self.screen_state.notice_passed:
                        self.screen_state.increment_count("team_select")
                    if not self.screen_state.purchase_screen_passed and self.screen_state.team_select_passed:
                        self.screen_state.increment_count("purchase_before_main_screen")
                    if not self.screen_state.main_screen_passed and self.screen_state.purchase_screen_passed:
                        self.screen_state.increment_count("main_screen")
                    if not self.screen_state.market_screen_passed and self.screen_state.main_screen_passed:
                        self.screen_state.increment_count("market_screen")
                    if not self.screen_state.get_item_screen_passed and self.screen_state.market_screen_passed:
                        self.screen_state.increment_count("get_item_screen")
                    if not self.screen_state.top_class_screen_passed and self.screen_state.get_all_btn_screen_passed:
                        self.screen_state.increment_count("top_class_screen")
                    
                    if self.password_handler.handle_password_screen(screen, loaded_templates, password_list, self.screen_state, deanak_id):
                        continue

                    if self.notice_handler.handle_notice_screen(screen, loaded_templates, self.screen_state, deanak_id):
                        continue
                        
                    if self.team_select_handler.handle_team_select_screen(screen, loaded_templates, self.screen_state, deanak_id):
                        continue
                        
                    if self.purchase_screen_handler.handle_purchase_screen(screen, loaded_templates, self.screen_state):
                        continue

                    if self.main_screen_handler.handle_main_screen(screen, loaded_templates, self.screen_state, deanak_id):
                        continue

                    if self.market_screen_handler.handle_market_screen(screen, loaded_templates, self.screen_state, deanak_id):
                        continue

                    if self.get_item_screen_handler.handle_get_item_screen(screen, loaded_templates, self.screen_state, deanak_id):
                        continue

                    if self.get_all_screen_handler.handle_get_all_screen(screen, loaded_templates, self.screen_state, deanak_id):
                        continue

                    if self.top_class_screen_handler.handle_top_class_screen(screen, loaded_templates, self.screen_state):
                        continue
                
                    if self.screen_state.top_class_screen_passed:
                        print("대낙 완료")
                        self.state.is_running = False
                        await self.remote.exit_program()
                        await asyncio.sleep(2)
                        # await self.remote.exit_remote()

                        await self.api.send_complete(deanak_id)

                        async with get_db_context() as db:
                            await self.remote_pcs_dao.update_tasks_request(db, server_id, "idle")
                        break

                    await asyncio.sleep(2)


                except (NoDetectionError, WrongPasswordError, TemplateEmptyError, APICallError, DuplicateLoginError) as e:
                    async with get_db_context() as db:
                        await self.remote_pcs_dao.update_tasks_request(db, server_id, "stopped")
                    self.state.is_running = False
                    return False
                except Exception as screen_error:
                    async with get_db_context() as db:
                        await self.remote_pcs_dao.update_tasks_request(db, server_id, "stopped")
                    self.error_handler.handle_error(screen_error, {"deanak_id": deanak_id}, user_message=self.error_handler.DEANAK_ERROR)
                    self.state.is_running = False
                    return False

        except (Exception, ValueError) as e:
            self.state.is_running = False
            raise DeanakError("대낙 작업 중 오류 - deanak_start함수 내")