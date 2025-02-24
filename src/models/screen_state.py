from dataclasses import dataclass
from typing import Dict

@dataclass
class ScreenState:
    """화면 상태를 관리하는 클래스"""
    # 화면 통과 상태
    anykey_passed: bool = False
    password_passed: bool = False
    notice_passed: bool = False
    team_select_passed: bool = False
    purchase_screen_passed: bool = False
    pc_icon_passed: bool = False
    main_screen_passed: bool = False
    market_screen_passed: bool = False
    get_item_screen_passed: bool = False
    arrange_btn_screen_passed: bool = False
    get_all_btn_screen_passed: bool = False
    top_class_screen_passed: bool = False
    # password_passed: bool = True
    # notice_passed: bool = True
    # team_select_passed: bool = True
    # purchase_screen_passed: bool = True
    # pc_icon_passed: bool = True
    # main_screen_passed: bool = True
    # market_screen_passed: bool = True
    # get_item_screen_passed: bool = True
    # arrange_btn_screen_passed: bool = True
    # get_all_btn_screen_passed: bool = True
    # top_class_screen_passed: bool = True

    exit_get_item_screen_passed: bool = False
    exit_main_screen_passed: bool = False
    exit_team_screen_passed: bool = False
    exit_modal_screen_passed: bool = False

    # 화면 감지 시도 횟수
    detection_counts: Dict[str, int] = None

    def __post_init__(self):
        if self.detection_counts is None:
            self.detection_counts = {
                "anykey": 0,
                "password": 0,
                "notice": 0,
                "team_select": 0,
                "purchase_before_main_screen": 0,
                "purchase_cancel_btn": 0,
                "pc_icon": 0,
                "main_screen": 0,
                "market_screen": 0,
                "get_item_screen": 0,
                "get_item_btn": 0,
                "arrange_btn": 0,
                "get_all_btn": 0,
                "top_class_screen": 0,
                "exit_get_item": 0,
                "exit_main": 0,
                "exit_team": 0,
                "exit_modal": 0
            }
    
    def increment_count(self, screen_name: str) -> None:
        """특정 화면의 감지 시도 횟수를 증가시킵니다."""
        if screen_name in self.detection_counts:
            self.detection_counts[screen_name] += 1

    def get_count(self, screen_name: str) -> int:
        """특정 화면의 감지 시도 횟수를 반환합니다."""
        return self.detection_counts.get(screen_name, 0)

    def reset_count(self, screen_name: str) -> None:
        """특정 화면의 감지 시도 횟수를 초기화합니다."""
        if screen_name in self.detection_counts:
            self.detection_counts[screen_name] = 0

    def reset_all(self) -> None:
        """모든 상태를 초기화합니다."""
        self.anykey_passed = False
        self.password_passed = False
        self.notice_passed = False
        self.team_select_passed = False
        self.purchase_screen_passed = False
        self.pc_icon_passed = False
        self.main_screen_passed = False
        self.market_screen_passed = False
        self.get_item_screen_passed = False
        self.arrange_btn_screen_passed = False
        self.get_all_btn_screen_passed = False
        self.top_class_screen_passed = False
        self.exit_get_item_screen_passed = False
        self.exit_main_screen_passed = False
        self.exit_team_screen_passed = False
        self.exit_modal_screen_passed = False

        for key in self.detection_counts:
            self.detection_counts[key] = 0
