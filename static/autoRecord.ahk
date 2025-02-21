#SingleInstance Force  ; 이전 인스턴스 자동 종료

Sleep(1200)

if WinExist("인터넷1") {
  WinActivate()
  ; 창이 활성화될 때까지 최대 3초 대기
  if !WinWaitActive("인터넷1", "", 3000) {
    MsgBox("창 활성화에 실패했습니다.")
    return
  }


  Send("^1")  ; Ctrl + 1 전송
  Send("{Tab}{Right 2}{Tab}{Enter}{Tab}{Tab}{Enter}")
} else {
  MsgBox("Chrome 창(제목: '인터넷1')을 찾을 수 없습니다.")
}
return