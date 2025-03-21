import os
from re import template
import cv2
from dotenv import load_dotenv
import requests
import numpy as np
from src.utils.image_matcher import ImageMatcher
from src.utils.error_handler import TemplateEmptyError

class TemplateService:
    def __init__(self, image_matcher: ImageMatcher):
        self.image_matcher = image_matcher
        load_dotenv()
        self.base_url = os.getenv("IMG_URL")
        self.base_url = self.base_url.rstrip('/')
        self.TEMPLATES = {
            # OTP 관련 템플릿
            "otp_frame": '/otpFrame.png',
            "otp_number": '/otpNumber.png',
            "otp_wrong": '/otpWrong.png',
            # 네이버 로그인 템플릿
            "naver_login": '/naverLoginBtn.png',
            "naver_login_grey": '/naverLoginBtnGrey.png',
            "naver_second_notify": '/naverSecondNotify.png',
            "naver_new_browser_login": '/naverNewBrowserLogin.png',
            # 대낙 관련 템플릿
            "anykey_screen": '/anykeyScreen.png',
            "password_screen": '/passwordScreen.png',
            "password_confirm": '/loginConfirm.png',
            "wrong_password": '/wrongPassword.png',
            "notice": '/notice.png',
            "team_select_screen": '/selectTeam.png',
            "team_select_text": '/selectTeamText.png',
            "team_select_icon": '/selectTeamIcon.png',
            "main_info_modal_screen": '/mainInfoModal.png',
            # "achivement_modal_before_main_screen": '/beforeMainAchivementModal.png',
            # "achivement_modal_cancel_btn": '/AchivementModalCloseBtn.png',
            "top_class_before_main_screen": '/beforeMainTopClass.png',
            "purchase_before_main_screen": '/beforeMainPurchases.png',
            "purchase_cancel_btn": '/purchaseCloseBtn.png',
            "pc_icon": '/pcIcon.png',
            "pc_icon_bar": '/pcIconBar.png',
            "main_screen": '/mainScreen.png',
            "market_screen": '/marketScreen.png',
            "market_full_screen": '/marketFullScreen.png',
            "market_btn": '/market.png',
            "get_item_screen": '/getItemScreen.png',
            "get_all_screen": '/getAllScreen.png',
            "list_btn": '/sellList.png',
            "get_item_btn": '/getItemConfirm.png',
            "arrange_btn_screen": '/priceArrangeScreen.png',
            "arrange_btn": '/priceArrangeBtn.png',
            "price_desc": '/priceDesc.png',
            "get_all_btn_screen": '/getAllScreen.png',
            "get_all_btn": '/getAll.png',
            "top_class_screen": '/noUseTopclassGetModal.png',
            "top_class_cancel_btn": '/noUseTopclassGetConfirm.png',
            # 대낙 종료 템플릿
            "exit_get_item": '/exitGetItemScreen.png',
            "exit_get_item_btn": '/exitGetItemBtn.png',
            "exit_main": '/pcIconBar.png',
            "exit_main_btn": '/exitMainBtn.png',
            "exit_team": '/selectTeamIcon.png',
            "exit_team_btn": '/exitTeamBtn.png',
            "exit_modal": '/exitModalScreen.png',
            "exit_modal_btn": '/exitModalBtn.png',
            # 중복 로그인 에러
            "connect_logged_in_id_error": "/connectLoggedInId.png",
            "same_login_in_anykey_error": '/atThatSameTimeInAnyKeyAndBeforeAccountExpire.png',
            "someone_already_login_error": '/duplicateConnection.png',
            "some_one_connecting_try_error": '/someOneConnect.png',
            "same_login_in_password_error": '/whenThroughPasswordButSomeOneInPassword.png',
            "some_one_otp_pass_error": '/whenFinishOTPpassButSomeOnePassOTPEither.png',
            "network_error": '/networkError.png'
        }
        
        self._template_cache = {}

    def _load_template(self, template_path: str):
        """서버에서 템플릿 이미지를 로드하고 캐싱"""
        try:
            # 캐시 확인
            if template_path in self._template_cache:
                return self._template_cache[template_path]

            # 서버에서 이미지 다운로드
            url = f"{self.base_url}{template_path}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"첫 번째 시도 실패 ({url}): {str(e)}")
                # 확장자 체크 후 변경
                if template_path.lower().endswith('.png'):
                    alt_path = template_path[:-4] + '.PNG'
                elif template_path.endswith('.PNG'):
                    alt_path = template_path[:-4] + '.png'
                
                url = f"{self.base_url}{alt_path}"
                print(f"두 번째 시도 ({url})")
                response = requests.get(url)
                response.raise_for_status()

            # 이미지 데이터를 numpy array로 변환
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            template = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if template is None:
                raise TemplateEmptyError(f"템플릿 이미지를 디코딩할 수 없습니다: {url}")

            # 캐시에 저장
            self._template_cache[template_path] = template
            return template

        except requests.RequestException as e:
            raise TemplateEmptyError(f"템플릿 다운로드 실패 (파일이 서버에 없을 수 있음): {str(e)}")
        except Exception as e:
            raise TemplateEmptyError(f"템플릿 로드 중 오류 발생: {str(e)}")

    # 개발 전용 로컬 템플릿 로드
    def _local_load_template(self, template_path: str):
        """로컬 static/img 폴더에서 템플릿 이미지를 로드하고 캐싱"""
        try:
            print(f"로컬 파일 로드: {template_path}")
            # 캐시 확인
            if template_path in self._template_cache:
                return self._template_cache[template_path]

            # 로컬 파일 경로 구성
            local_path = os.path.join('static', 'img', template_path.lstrip('/'))
            
            try:
                # 첫 번째 시도
                template = cv2.imread(local_path, cv2.IMREAD_COLOR)
                if template is None:
                    # 확장자 체크 후 변경
                    if local_path.lower().endswith('.png'):
                        alt_path = local_path[:-4] + '.PNG'
                    elif local_path.endswith('.PNG'):
                        alt_path = local_path[:-4] + '.png'
                    else:
                        # 다른 확장자인 경우 기본값으로 .png 사용
                        alt_path = local_path[:-4] + '.png'
                    
                    print(f"첫 번째 시도 실패 ({local_path}), 두 번째 시도 ({alt_path})")
                    template = cv2.imread(alt_path, cv2.IMREAD_COLOR)

            except Exception as e:
                print(f"이미지 로드 실패: {str(e)}")
                raise

            if template is None:
                raise TemplateEmptyError(f"템플릿 이미지를 로드할 수 없습니다: {local_path}")

            # 캐시에 저장
            self._template_cache[template_path] = template
            return template

        except Exception as e:
            raise TemplateEmptyError(f"템플릿 로드 중 오류 발생: {str(e)}")


    def load_templates(self, template_keys: list):
        """지정된 키에 해당하는 템플릿 이미지들을 로드
        
        Args:
            template_keys (list): 로드할 템플릿 키 목록 (예: ["otp_frame", "otp_number"])
            
        Returns:
            dict: 템플릿 키와 로드된 이미지의 딕셔너리
            
        Raises:
            Exception: 템플릿 파일이 없거나 로드 실패시
        """
        templates = {}
        for key in template_keys:
            if key not in self.TEMPLATES:
                raise TemplateEmptyError(f"존재하지 않는 템플릿 키: {key}")
                
            path = self.TEMPLATES[key]
            template = self._load_template(path)
            # template = self._local_load_template(path)
            if template is None:
                raise TemplateEmptyError(f"템플릿 로드 실패: {path}")
                
            templates[key] = template
            
        return templates

    def load_password_templates(self, password_list: list):
        """비밀번호 템플릿 로드"""
        templates = {}
        for password in password_list:
            path = f'/{password}.png'
            template = self._load_template(path)
            # template = self._local_load_template(path)
            if template is None:
                raise TemplateEmptyError(f"비밀번호 템플릿 로드 실패: {path}")
            templates[password] = template
        return templates

    def get_templates(self, password_list: list = None):
        """모든 템플릿 이미지를 로드하고 반환합니다.

        Args:
            password_list (list, optional): 비밀번호 템플릿을 로드할 비밀번호 목록. Defaults to None.

        Returns:
            dict: 모든 템플릿 키와 로드된 이미지의 딕셔너리

        Raises:
            TemplateEmptyError: 템플릿 파일이 없거나 로드 실패시
        """
        try:
            templates = {}
            
            # 기본 템플릿 로드
            for key in self.TEMPLATES.keys():
                path = self.TEMPLATES[key]
                
                # 캐시된 템플릿이 있으면 사용
                if path in self._template_cache:
                    templates[key] = self._template_cache[path]
                    continue
                
                
                # 템플릿 파일 존재 확인
                # 서버에서 이미지를 다운로드 받기 때문에 파일 존재 확인 불필요

                # 템플릿 로드
                template = self._load_template(path)
                # template = self._local_load_template(path)
                if template is None:
                    raise TemplateEmptyError(f"템플릿 로드에 실패했습니다: {path}")
                
                templates[key] = template
                self._template_cache[path] = template  # 캐시에 저장
            
            # 비밀번호 템플릿 로드
            if password_list:
                password_templates = self.load_password_templates(password_list)
                templates["password_templates"] = password_templates
                
            if not templates:
                raise TemplateEmptyError("로드된 템플릿이 없습니다.")
                
            return templates
            
        except Exception as e:
            if isinstance(e, TemplateEmptyError):
                raise
            raise TemplateEmptyError(f"템플릿 로드 중 오류 발생: {str(e)}")

    def clear_cache(self):
        """템플릿 캐시 초기화"""
        self._template_cache.clear()