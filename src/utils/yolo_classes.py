# YOLO 클래스 매핑
YOLO_CLASSES = {
    "otp_frame": 0,
    "otp_number": 1,
    "otp_wrong": 2,
    "naver_login": 3,
    "naver_login_grey": 4,
    "anykey_screen": 5,
    "password_screen": 6,
    "password_confirm": 7,
    "wrong_password": 8,
    "notice": 9,
    "team_select_screen": 10,
    "team_select_text": 11,
    "team_select_icon": 12,
    "main_info_modal_screen": 13,
    "top_class_before_main_screen": 14,
    "purchase_before_main_screen": 15,
    "purchase_cancel_btn": 16,
    "pc_icon": 17,
    "pc_icon_bar": 18,
    "main_screen": 19,
    "market_screen": 20,
    "market_full_screen": 21,
    "market_btn": 22,
    "get_item_screen": 23,
    "get_all_screen": 24,
    "list_btn": 25,
    "get_item_btn": 26,
    "arrange_btn_screen": 27,
    "arrange_btn": 28,
    "price_desc": 29,
    "get_all_btn_screen": 30,
    "get_all_btn": 31,
    "top_class_screen": 32,
    "top_class_cancel_btn": 33,
    "exit_get_item": 34,
    "exit_get_item_btn": 35,
    "exit_main": 36,
    "exit_main_btn": 37,
    "exit_team": 38,
    "exit_team_btn": 39,
    "exit_modal": 40,
    "exit_modal_btn": 41,
    "same_login_in_anykey_error": 42,
    "someone_already_login_error": 43,
    "some_one_connecting_try_error": 44,
    "same_login_in_password_error": 45,
    "some_one_otp_pass_error": 46,
    "network_error": 47,
    "0": 48,
    "1": 49,
    "2": 50,
    "3": 51,
    "4": 52,
    "5": 53,
    "6": 54,
    "7": 55,
    "8": 56,
    "9": 57
}


def get_yolo_class_id(template_key):
    """템플릿 키값에 해당하는 YOLO 클래스 ID를 반환

    Args:
        template_key (str): 템플릿 키값

    Returns:
        int: YOLO 클래스 ID. 키값이 없는 경우 None 반환
    """
    return YOLO_CLASSES.get(template_key)
