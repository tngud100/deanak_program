import asyncio
from os import error

from sqlalchemy.orm import context, exc
from src import state
from database import get_db_context
from src.service.do_service import DoService
from src.service.otp_service import OTPService
from src.service.template_service import TemplateService
from src.service.auto_deanak import AutoDeanak
from src.utils.api import Api
from src.utils.remote_controller import RemoteController
from src.utils.error_handler import DuplicateLoginError, ErrorHandler, ControllerError, DeanakError, OTPError, OTPTimeoutError, OTPOverTimeDetectError, NoDetectionError, TemplateEmptyError, NoWorkerError, CantFindPcNumError, CantFindRemoteProgram
from src.dao.remote_pcs_dao import RemoteDao
from src.dao.deanak_dao import DeanakDao
from src.utils.image_matcher import ImageMatcher
from src.utils.capture import CaptureUtil
from src.utils.input_controller import InputController

# 공통으로 사용할 객체들 초기화
image_matcher = ImageMatcher()
capture = CaptureUtil()
input_controller = InputController()
remote = RemoteController()
error_handler = ErrorHandler()
remote_pcs_dao = RemoteDao()
deanak_dao = DeanakDao()
unique_id = state.unique_id()
api = Api()

# 서비스 객체들 초기화
template_service = TemplateService(image_matcher)
otp_service = OTPService(image_matcher, capture, input_controller, template_service)
auto_deanak = AutoDeanak(image_matcher, input_controller, remote, template_service, capture, state, remote_pcs_dao)
do_service = DoService(remote, error_handler, state, remote_pcs_dao, deanak_dao, otp_service, auto_deanak)

async def do_task(request, deanak_info:dict=None):
    """대낙 태스크 실행"""
    print(f"태스크 실행: request={request}, deanak_state={deanak_info['deanak_state']}")
    context = {"deanak_id": deanak_info['deanak_id'], "worker_id": deanak_info['worker_id']}
    try:
        server_id = await unique_id.read_unique_id()
            
        if request == "otp_check":
            # 작업 상태 업데이트
            async with get_db_context() as db:
                await remote_pcs_dao.update_tasks_request(db, server_id, "working")
                
            await api.send_start(deanak_info['deanak_id'])
            print("state = working으로 변경")

            await asyncio.sleep(15)
            if not await do_otp(deanak_info, server_id):
                return False
            
            print("otp 인식 완료, 15초 뒤 대낙 작업 시작")
            return await do_task("deanak_start", deanak_info)

        if request == "deanak_start":
            
            if not deanak_info['otp']:
                # 작업 상태 업데이트
                async with get_db_context() as db:
                    await remote_pcs_dao.update_tasks_request(db, server_id, "working")
                await api.send_start(deanak_info['deanak_id'])
                print("state = working으로 변경")

            print("게임이 켜지기까지 기다리는 중...")
            await asyncio.sleep(5)
            if not await do_deanak(deanak_info, server_id):
                return False
        
        # return await pending_task()
    
    except TemplateEmptyError as e:
        await update_error_status(server_id, e, context, error_handler.TEMPLATE_EMPTY_ERROR)
        return False
    except NoWorkerError as e:
        await update_error_status(server_id, e, context, error_handler.NO_WORKER_ERROR)
        return False
    except CantFindPcNumError as e:
        await update_error_status(server_id, e, context, error_handler.CANT_FIND_PC_NUM_ERROR)
        return False
    except CantFindRemoteProgram as e:
        await update_error_status(server_id, e, context, error_handler.CANT_FIND_REMOTE_PROGRAM)
        return False

    except Exception as e:
        raise ControllerError(f"do_task 작업 실패 - 알수 없는 오류")


async def pending_task():
    """대기 중인 요청 처리"""
    try:
        while not state.pending_services.empty():
            next_request = await state.pending_services.get()
            print(f"대기 중이던 요청 처리 시작: worker_id={next_request['worker_id']}")
            await do_task(
                next_request['request'],
                next_request['deanak_info']
            )
    except Exception as e:
        error_handler.handle_error(e)
        print(f"대기 중인 요청 처리 중 오류 발생: {e}")
    

async def do_otp(deanak_info, server_id):
    """otp를 포함한 대낙 태스크 실행"""
    context = {"deanak_id": deanak_info['deanak_id'], "worker_id": deanak_info['worker_id']}
    try:
        return await do_service.check_otp(deanak_info)

    except OTPOverTimeDetectError as e:
        await update_error_status(server_id, e, context, error_handler.OTP_OVER_TIME_DETECT)
        return False
    except OTPTimeoutError as e:
        await update_error_status(server_id, e, context, error_handler.OTP_TIME_OUT)
        return False
    except NoDetectionError as e:
        await update_error_status(server_id, e, context, error_handler.NO_DETECT_OTP_SCENE)
        return False
    except (OTPError, ValueError) as e:
        await update_error_status(server_id, e, context, error_handler.OTP_ERROR)
        return False
    except (TemplateEmptyError, NoWorkerError, CantFindPcNumError, CantFindRemoteProgram) as e:
        raise
    except Exception as e:
        raise ControllerError(f"otp 작업 중 오류 - do_task함수")


async def do_deanak(deanak_info, server_id):
    """대낙 태스크 실행"""
    context = {"deanak_id": deanak_info['deanak_id'], "worker_id": deanak_info['worker_id']}
    try:
        return await do_service.execute_deanak(deanak_info)

    except (TemplateEmptyError, NoWorkerError, CantFindPcNumError, CantFindRemoteProgram) as e:
        raise

    except (DeanakError, ValueError) as e:
        await update_error_status(server_id, e, context, error_handler.DEANAK_ERROR)
        return False    
    except Exception as e:
        raise ControllerError(f"deanak 작업 중 오류 - do_task함수")


async def update_error_status(server_id, e, context, ErrorMessage):
    """에러 처리"""
    async with get_db_context() as db:
        await remote_pcs_dao.update_tasks_request(db, server_id, "stopped")
    error_handler.handle_error(e, context=context, critical=True, user_message=ErrorMessage)

async def stop_deanak():
    """대낙 태스크 중지"""
    return await do_service.stop_deanak()