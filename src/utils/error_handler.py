import logging
from re import T
import traceback
from datetime import datetime
import os
from database import get_db_context
from src.dao.remote_pcs_dao import RemoteDao
from src import state
from src.models import deanak
from src.utils.api import Api as ApiClass  # api 클래스를 ApiClass로 import
import asyncio

class WrongPasswordError(Exception):
    pass
class DeanakError(Exception):
    pass
class MessageSendFail(Exception):
    pass


class NaverSecondCertifyError(Exception):
    pass
class DuplicateLoginError(Exception):
    pass
class ControllerError(Exception):
    pass
class APICallError(Exception):
    pass
class NoDetectionError(Exception):
    pass
class NoDetectionPCIconError(Exception):
    pass
class TemplateEmptyError(Exception):
    pass
class NoWorkerError(Exception):
    pass
class CantFindPcNumError(Exception):
    pass
class CantFindRemoteProgram(Exception):
    pass

class SkipPurchaseException(Exception):
    pass
class SkipTopClassException(Exception):
    pass

class OTPTimeoutError(Exception):
    pass
class OTPOverTimeDetectError(Exception):
    pass
class OTPError(Exception):
    pass


class ErrorHandler:
    API_CALL_ERROR = "심플 API 호출 실패"

    TEMPLATE_EMPTY_ERROR = "템플릿 로드 중 오류 발생"
    NO_WORKER_ERROR = "작업자 찾을 수 없습니다"
    CANT_FIND_PC_NUM_ERROR = "PC 번호를 찾을 수 없습니다"
    CANT_FIND_REMOTE_PROGRAM = "원격 프로그램 찾을 수 없습니다"
    CONTROLLER_ERROR = "contoller파일 내에서 알 수 없는 오류 발생"
    HANDLER_ERROR = "handler파일 내에서 알 수 없는 오류 발생"

    NO_DETECT_OTP_SCENE = "otp 화면 탐지 실패"
    OTP_OVER_TIME_DETECT = "otp 탐지 횟수를 초과하였습니다"
    OTP_TIME_OUT = "otp 인증 시간을 초과하였습니다"
    OTP_ERROR = "otp에서 알 수 없는 오류 발생"

    NAVER_SECOND_CERTIFY_ERROR = "네이버 2차 인증이 존재"

    SAME_START_ERROR_BY_ANYKEY_SCENE = "인게임 동시 접속으로 인한 오류(위치 : AnyKeyScene)"
    DUPLICATE_CONNECTING_ERROR = "이미 로그인되어 있는 계정에 로그인 시도"
    SOMEONE_CONNECT_TRY_ERROR = "계정 사용자가 중복 로그인을 시도"
    SAME_START_ERROR_BY_PASSWORD_SCENE = "인게임 동시 접속으로 인한 오류(위치 : PasswordScene)"
    DUPLICATE_OTP_CHECK_ERROR = "OTP처리 중 다른 사용자가 중복으로 OTP 체크을 시도"
    NETWORK_ERROR = "불안정한 네트워크"

    WRONG_PASSWORD_ERROR = "2차 비밀번호 틀림"
    NO_DETECT_INITIAL_SCREEN = "초기 화면 탐지 실패"
    NO_DETECT_ANYKEY_SCENE = "첫번째 화면 탐지 실패"
    NO_DETECT_PASSWORD_SCENE = "비밀번호 화면 탐지 실패"
    NO_DETECT_NOTICE_SCENE = "공지 화면 탐지 실패"
    NO_DETECT_TEAM_SELECT_SCENE = "팀선택 화면 탐지 실패"
    NO_DETECT_PURCHASE_SCREEN_SCENE = "구매 화면 탐지 실패"
    NO_DETECT_MAIN_SCREEN_SCENE = "메인 화면 탐지 실패(이적 시장 버튼 탐지 실패)"
    NO_DETECT_PC_ICON = "PC 스티커 탐지 실패"
    NO_DETECT_MARKET_SCREEN_SCENE = "마켓 화면 탐지 실패(판매 리스트 버튼 탐지 실패 혹은 비정상 감지)"
    NO_DETECT_GET_ITEM_SCREEN_SCENE = "이적 시장의 판매 리스트 화면 탐지 실패(모두 받기 버튼 탐지 실패 또는 대낙 받을 판매된 선수 없을 경우)"
    NO_DETECT_GET_ALL_SCREEN_SCENE = "모두 받기 화면 탐지 실패(정렬 혹은 받기 버튼 탐지 실패)"
    NO_DETECT_EXIT_GAME_SCREEN_SCENE = "게임 종료 화면 탐지 실패(get_item, main, team, exit_modal 중 탐지 실패)"
    DEANAK_ERROR = "대낙 작업 중 오류 - 무한 로직(WHILE) 내"
    EMPTY_PASSWORD_TEMPLATE = "비밀번호 템플릿을 찾을 수 없습니다"
    
    def __init__(self):
        self.log_dir = "logs/error"
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_logger()
        self.remote_pcs_dao = RemoteDao()
        self.unique_id = state.unique_id()
        self.api_instance = ApiClass()  # ApiClass 사용
        self.user_message = {
            '': [
                self.TEMPLATE_EMPTY_ERROR,
                self.NO_WORKER_ERROR,
                self.CANT_FIND_PC_NUM_ERROR,
                self.CANT_FIND_REMOTE_PROGRAM,
                self.CONTROLLER_ERROR,
                self.HANDLER_ERROR,
                self.DEANAK_ERROR,
                self.EMPTY_PASSWORD_TEMPLATE,
                self.OTP_ERROR,
            ],
            '인식 횟수 초과': [self.OTP_OVER_TIME_DETECT],
            '인증 시간 초과': [self.OTP_TIME_OUT],

            '네이버 2차 인증': [self.NAVER_SECOND_CERTIFY_ERROR],
            '인게임 동시 접속': [self.SAME_START_ERROR_BY_ANYKEY_SCENE],
            '이미 로그인되어 있는 계정': [self.DUPLICATE_CONNECTING_ERROR],
            '고객이 중복 로그인을 시도': [self.SOMEONE_CONNECT_TRY_ERROR],
            '인게임 동시 접속': [self.SAME_START_ERROR_BY_PASSWORD_SCENE],
            '고객이 중복 OTP 시도': [self.DUPLICATE_OTP_CHECK_ERROR],
            '네트워크 에러': [self.NETWORK_ERROR],

            '2차 비밀번호 틀림': [self.WRONG_PASSWORD_ERROR],
            'otp 혹은 비밀번호 화면': [self.NO_DETECT_INITIAL_SCREEN],
            'OTP': [self.NO_DETECT_OTP_SCENE],
            '인트로 화면': [self.NO_DETECT_ANYKEY_SCENE],
            '비밀번호 화면': [self.NO_DETECT_PASSWORD_SCENE],
            'PC방 혜택': [self.NO_DETECT_PC_ICON],
            '공지사항 화면': [self.NO_DETECT_NOTICE_SCENE],
            '팝업 화면': [self.NO_DETECT_PURCHASE_SCREEN_SCENE],
            '팀 선택 화면': [self.NO_DETECT_TEAM_SELECT_SCENE],
            '프리룸 화면': [self.NO_DETECT_MAIN_SCREEN_SCENE],
            '이적시장 화면': [self.NO_DETECT_MARKET_SCREEN_SCENE],
            '이적시장의 거래목록': [self.NO_DETECT_GET_ITEM_SCREEN_SCENE],
            '모두받기 화면': [self.NO_DETECT_GET_ALL_SCREEN_SCENE],
            '대낙 완료 후 화면': [self.NO_DETECT_EXIT_GAME_SCREEN_SCENE],
        }
        self.error_messages = {
            '프로그램': [
                self.API_CALL_ERROR,
                self.TEMPLATE_EMPTY_ERROR,
                self.NO_WORKER_ERROR,
                self.CANT_FIND_PC_NUM_ERROR,
                self.CANT_FIND_REMOTE_PROGRAM,
                self.CONTROLLER_ERROR,
                self.HANDLER_ERROR,
                self.DEANAK_ERROR,
                self.EMPTY_PASSWORD_TEMPLATE,
                self.OTP_ERROR,
                self.NETWORK_ERROR
            ],
            '로그인': [
                self.SAME_START_ERROR_BY_ANYKEY_SCENE,
                self.DUPLICATE_CONNECTING_ERROR,
                self.SAME_START_ERROR_BY_PASSWORD_SCENE,
                self.SOMEONE_CONNECT_TRY_ERROR,
                self.DUPLICATE_OTP_CHECK_ERROR,
                self.NAVER_SECOND_CERTIFY_ERROR
            ],
            'OTP': [
                self.OTP_OVER_TIME_DETECT,
                self.OTP_TIME_OUT,
            ],
            '비밀번호': [self.WRONG_PASSWORD_ERROR],
            '탐지 실패':[
                self.NO_DETECT_INITIAL_SCREEN,
                self.NO_DETECT_OTP_SCENE,
                self.NO_DETECT_ANYKEY_SCENE,
                self.NO_DETECT_PASSWORD_SCENE,
                self.NO_DETECT_NOTICE_SCENE,
                self.NO_DETECT_PC_ICON,
                self.NO_DETECT_TEAM_SELECT_SCENE,
                self.NO_DETECT_MARKET_SCREEN_SCENE,
                self.NO_DETECT_GET_ITEM_SCREEN_SCENE,
                self.NO_DETECT_GET_ALL_SCREEN_SCENE,
                self.NO_DETECT_EXIT_GAME_SCREEN_SCENE
            ],
            # '게임실행 오류': [self.NO_DETECT_PASSWORD_SCENE],
            # '팀 선택 화면 오류': [self.NO_DETECT_NOTICE_SCENE],
            # '메인 화면 오류': [self.NO_DETECT_MAIN_SCREEN_SCENE],
            # '마켓 화면 오류': [self.NO_DETECT_MARKET_SCREEN_SCENE],
            # '이적 시장의 판매 리스트 화면 오류': [self.NO_DETECT_GET_ITEM_SCREEN_SCENE],
            # '모두 받기 화면 오류': [self.NO_DETECT_GET_ALL_SCREEN_SCENE],
            # '대낙 작업 중 오류': [self.DEANAK_ERROR],
            # '비밀번호 템플릿을 찾을 수 없습니다': [self.EMPTY_PASSWORD_TEMPLATE]
        }

    def setup_logger(self):
        """로거 설정"""
        log_file = os.path.join(self.log_dir, f"error_{datetime.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'  # UTF-8 인코딩 설정
        )

    def handle_error(self, error, context=None, critical=False, user_message=None):
        """에러 처리"""
        try:
            # 오류 메시지 포맷 설정
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            exception_type = type(error).__name__
            tb = traceback.format_exc()  # 전체 스택 트레이스를 문자열로 변환
            context_str = context if context else ""
            full_message = (
                f"Timestamp: {timestamp}\n"
                f"Exception Type: {exception_type}\n"
                f"Context: {context_str}\n"
                f"Error Message: {user_message}\n"
                f"Error Details: {error}\n"
                f"Traceback:\n{tb}\n"
                + "-"*80 + "\n"
            )
            # print(f"full_message: {full_message}")
            # 로그 기록
            logging.error(full_message)
            
            # 심각한 에러 처리
            if critical:
                print("Critical error occurred.")
        
            # 사용자에게 알림
            if user_message:
                error_key = self.get_error_key(user_message)
                message_key = self.get_message_key(user_message)

                if error_key:
                    print(f"{error_key}: {message_key}")
                    deanak_id = context.get('deanak_id')
                    if deanak_id is None:
                        raise MessageSendFail("deanak_id가 없음")

                    asyncio.create_task(self.api_instance.send_error(deanak_id, error_key, message_key))

            return {
                'error': str(error),
                'context': context,
                'timestamp': datetime.now().isoformat()
            }

        except MessageSendFail as e:
            print(f"사용자에게 알림을 보내는 중 오류 발생: {e}")
            return None
        except Exception as e:
            print(f"ErrorHandler에서 오류 발생: {e}")
            return None

    def get_message_key(self, message):
        for key, value in self.user_message.items():
            if message in value:
                return key
        return ""

    def get_error_key(self, message):
        """주어진 에러 메시지에 해당하는 키를 반환합니다."""
        for key, value in self.error_messages.items():
            if message in value:
                return key
        return ""

    def get_error_logs(self, date=None):
        """에러 로그 조회"""
        try:
            if date:
                log_file = os.path.join(self.log_dir, f"error_{date}.log")
            else:
                log_file = os.path.join(self.log_dir, f"error_{datetime.now().strftime('%Y%m%d')}.log")
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    return f.readlines()
            return []
        except Exception as e:
            print(f"로그 조회 중 오류 발생: {e}")
            return []
