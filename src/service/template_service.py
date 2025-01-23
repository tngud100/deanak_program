import os
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
        self.base_url = os.getenv("IMG_URL");
        self.base_url = self.base_url.rstrip('/')
        self.TEMPLATES = {
            # OTP 관련 템플릿
            "otp_frame": '/otpFrame.PNG',
            "otp_number": '/otpNumber.PNG',
            "otp_wrong": '/otpWrong.PNG',
            # 대낙 관련 템플릿
            "password_screen": '/passwordScreen.PNG',
            "password_confirm": '/loginConfirm.PNG',
            "wrong_password": '/wrongPassword.PNG',
            "team_select_screen": '/selectTeam.PNG',
            "team_select_text": '/selectTeamText.PNG',
            "purchase_before_main_screen": '/beforeMainPurchases.PNG',
            "purchase_cancel_btn": '/purchaseCloseBtn.PNG',
            "main_screen": '/mainScreen.PNG',
            "market_screen": '/marketScreen.PNG',
            "get_item_screen": '/getItemScreen.PNG',
            "get_all_screen": '/getAllScreen.PNG',
            "market_btn": '/market.PNG',
            "list_btn": '/sellList.PNG',
            "get_item_btn": '/getItemConfirm.PNG',
            "arrange_btn_screen": '/PriceArrangeScreen.PNG',
            "arrange_btn": '/priceArrangeBtn.PNG',
            "price_desc": '/priceDesc.PNG',
            "get_all_btn_screen": '/getAllScreen.PNG',
            "get_all_btn": '/getAll.PNG',
            "top_class_screen": '/noUseTopclassGetModal.PNG',
            "top_class_cancel_btn": '/noUseTopclassGetConfirm.PNG',
            # 중복 로그인 에러
            "same_login_in_anykey_error": '/atThatSameTimeInAnyKeyAndBeforeAccountExpire.png',
            "someone_already_login_error": '/duplicateConnection.png',
            "some_one_connecting_try_error": '/someOneConnect.png',
            "same_login_in_password_error": '/whenThroughPasswordButSomeOneInPassword.png',
            "some_one_otp_pass_error": '/whenFinishOTPpassButSomeOnePassOTPEither.png'
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
            response = requests.get(url)
            response.raise_for_status()  # 에러 체크

            # 이미지 데이터를 numpy array로 변환
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            template = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)

            if template is None:
                raise TemplateEmptyError(f"Failed to load template from {url}")

            # 캐시에 저장
            self._template_cache[template_path] = template
            return template

        except requests.RequestException as e:
            raise TemplateEmptyError(f"Failed to download template from {url}: {str(e)}")
        except Exception as e:
            raise TemplateEmptyError(f"Error loading template {url}: {str(e)}")

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
            if template is None:
                raise TemplateEmptyError(f"템플릿 로드 실패: {path}")
                
            templates[key] = template
            
        return templates

    def load_password_templates(self, password_list: list):
        """비밀번호 템플릿 로드"""
        templates = {}
        for password in password_list:
            path = f'/{password}.PNG'
            template = self._load_template(path)
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
