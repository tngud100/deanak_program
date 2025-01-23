import asyncio
from src.utils.api import Api
from src.utils.remote_controller import RemoteController
from src.utils.error_handler import CantFindRemoteProgram, DuplicateLoginError, ErrorHandler, DeanakError, OTPError, NoWorkerError, CantFindPcNumError, OTPTimeoutError, NoDetectionError, OTPOverTimeDetectError, TemplateEmptyError
from src.dao.remote_pcs_dao import RemoteDao
from src.dao.deanak_dao import DeanakDao
from src.service.auto_deanak import AutoDeanak
from database import get_db_context
from src.service.otp_service import OTPService
from src import state

class DoService:
    def __init__(self, remote: RemoteController, error_handler: ErrorHandler, state: state,
                 remote_pcs_dao: RemoteDao, deanak_dao: DeanakDao, otp_service: OTPService, auto_deanak: AutoDeanak):
        self.remote = remote
        self.error_handler = error_handler
        self.remote_pcs_dao = remote_pcs_dao
        self.otp_service = otp_service
        self.auto_deanak = auto_deanak
        self.deanak_dao = deanak_dao
        self.state = state
        self.api = Api()

    async def _validate_worker(self, db, server_id, worker_id):
        """worker_id 검증 및 PC 번호 조회"""
        worker_exists = await self.remote_pcs_dao.check_worker_exists(db, server_id, worker_id)
        if not worker_exists:
            raise NoWorkerError("해당 worker_id가 remote_pcs테이블에 존재하지 않습니다.")

        pc_num = await self.remote_pcs_dao.get_pc_num_by_worker_id(db, worker_id)
        if pc_num is None:
            raise CantFindPcNumError("PC 번호를 찾을 수 없습니다.")
        
        return pc_num

    async def check_otp(self, deanak_info:dict=None):
        """OTP 체크 및 검증"""
        try:
            server_id = await self.state.unique_id().read_unique_id()
            worker_id = deanak_info['worker_id']
            deanak_id = deanak_info['deanak_id']
            already_send_otp = None
            wrong_otp_state = False
            renew_otp = False # otp번호 갱신
            
            # 타이머 설정
            start_time = asyncio.get_event_loop().time()
            timeout_duration = 135  # 2분
            renew_duration = 65

            async with get_db_context() as db:
                pc_num = await self._validate_worker(db, server_id, worker_id)
                
            # 원격 연결 시작
            if not await self.remote.start_remote(pc_num):
                return False

            # 2분 동안만 실행
            while (asyncio.get_event_loop().time() - start_time) < timeout_duration:
                current_time = asyncio.get_event_loop().time()
                elapsed_time = current_time - start_time

                # OTP 확인 통과 체크
                async with get_db_context() as db:
                    otp_pass = await self.deanak_dao.get_otp_pass_by_deanak_id(db, deanak_id)

                if otp_pass == 1:
                    break

                # OTP를 보내지 않았면 OTP 추출
                if already_send_otp is None:
                        # OTP 추출
                        otp_text = await self.otp_service.capture_and_extract_otp()
                        if not otp_text:  # None이거나 빈 문자열인 경우
                            print("OTP 추출 실패")
                            print("다시 인식을 시작합니다")
                            continue
                        
                        # OTP 보내기
                        if await self.api.send_otp(deanak_id, otp_text):
                            already_send_otp = otp_text

                if already_send_otp is not None:
                    is_state_check = await self.otp_service.pass_or_wrong_otp_detect() # 0이면 이상 없음, 1이면 통과, -1이면 틀림

                # 통과로 state업데이트
                if is_state_check == 1:
                    print("OTP 통과, 게임 실행")
                    async with get_db_context() as db:
                        await self.deanak_dao.update_otp_pass(db, deanak_id, 1)

                if is_state_check == 0:
                    print("사용자의 입력이 {}/{}번 틀렸습니다.".format(0, 1))
                    print("사용자의 입력을 기다리고 있습니다.")

                if is_state_check == -1 and wrong_otp_state:
                    print("사용자의 입력이 {}/{}번 틀렸습니다.".format(1, 1))
                    print("사용자의 입력을 기다리고 있습니다.")
    
                # 사용자가 틀렸을시 다시 OTP 추출하여 보내도록 하는 로직
                if not wrong_otp_state and is_state_check == -1:
                    print("다시 감지를 시작합니다")
                    wrong_otp_state = True
                    already_send_otp = None    # OTP 재시도를 위해 초기화

                    # 틀렸을시 시간을 60초 빼고 새롭게 갱신
                    if elapsed_time >= renew_duration:
                        start_time = current_time - renew_duration
                    else:
                        start_time = current_time
                

                # 60초가 경과하여 새롭게 OTP가 바뀐 경우
                if elapsed_time >= renew_duration and not renew_otp:
                    print(f"60초가 경과하여 OTP 갱신이 필요합니다. (경과 시간: {int(elapsed_time)}초)")
                    renew_otp = True
                    already_send_otp = None
                
                # 3초마다 사용자의 입력을 확인
                await asyncio.sleep(3)

            # 2분이 지나도 OTP가 통과되지 않은 경우
            if not otp_pass:
                print(f"OTP 인증 시간 초과 (총 경과 시간: {int(asyncio.get_event_loop().time() - start_time)}초)")
                raise OTPTimeoutError("OTP 인증 시간 초과")

            # 원격 나가기
            # await self.remote.exit_remote()

            return otp_text

        except (OTPTimeoutError, ValueError, NoDetectionError, OTPOverTimeDetectError,
                NoDetectionError, TemplateEmptyError, NoWorkerError, CantFindPcNumError,
                CantFindRemoteProgram) as e:
            raise

        except Exception as e:
            # 알 수 없는 예외만 OTPError로 감싸기
            raise OTPError(f"OTP 감지 중 알 수 없는 오류 발생: {str(e)}")

    async def execute_deanak(self, deanak_info:dict=None):
        """DO 실행 로직"""
        try:
            server_id = await self.state.unique_id().read_unique_id()
            worker_id = deanak_info['worker_id']

            # async with get_db_context() as db:
            #     pc_num = await self._validate_worker(db, server_id, worker_id)

            # # 원격 연결 시작
            # if not await self.remote.start_remote(pc_num):
            #     return False

            # 자동 대낙 프로그램 실행
            self.state.is_running = True  # Task 시작 전에 실행 상태 초기화
            self.state.service_running_task = asyncio.create_task(self.auto_deanak.deanak_start(deanak_info))
            
            success = await self.state.service_running_task
            
            if not success:
                return False

            return True

        except (DeanakError, ValueError, TemplateEmptyError, NoWorkerError,
                CantFindPcNumError, CantFindRemoteProgram) as e:
            raise

        except Exception as e:
            raise DeanakError(f"대낙 작업 중 알 수 없는 오류 - execute_deanak 함수 내")

    async def stop_deanak(self):
        """대낙 작업 중단"""
        self.state.is_running = False
        if self.state.service_running_task:
            try:
                await self.state.service_running_task
            except asyncio.CancelledError:
                pass  # 태스크가 취소되어도 정상적으로 처리
            finally:
                self.state.service_running_task = None
