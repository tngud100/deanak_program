import pyautogui
import keyboard
import time

class InputController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        self.default_delay = 0.1

    def click(self, x, y, clicks=1):
        """마우스 클릭"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 먼저 마우스를 목표 위치 근처로 천천히 이동
                pyautogui.moveTo(x, y, duration=0.5)
                time.sleep(0.2)  # 잠시 대기
                pyautogui.click(x=x, y=y, clicks=clicks)
                time.sleep(self.default_delay)
                return
            except pyautogui.FailSafeException as e:
                if attempt < max_retries - 1:
                    print(f"마우스 이동 중 fail-safe 발생. {retry_delay}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print("최대 재시도 횟수 초과")
                    raise e
            except Exception as e:
                print(f"마우스 클릭 중 오류 발생: {e}")
                raise e

    def press_key(self, key):
        """키 입력"""
        try:
            keyboard.press_and_release(key)
            time.sleep(self.default_delay)
        except Exception as e:
            print(f"키 입력 중 오류 발생: {e}")
            raise e;

    def hotkey(self, *args):
        """단축키 입력"""
        try:
            # 모든 키를 누름
            for key in args:
                keyboard.press(key)
                time.sleep(0.1)  # 각 키 입력 사이에 약간의 딜레이
            
            # 역순으로 키를 뗌
            for key in reversed(args):
                keyboard.release(key)
                time.sleep(0.1)
            
            time.sleep(self.default_delay)
            return True
        except Exception as e:
            print(f"단축키 입력 중 오류 발생: {e}")
            # 에러 발생 시 모든 키를 떼줌
            for key in args:
                try:
                    keyboard.release(key)
                except:
                    pass
            raise e

    def type_text(self, text):
        """텍스트 입력"""
        try:
            pyautogui.typewrite(text, interval=0.05)
            time.sleep(self.default_delay)
            return True
        except Exception as e:
            print(f"텍스트 입력 중 오류 발생: {e}")
            raise e