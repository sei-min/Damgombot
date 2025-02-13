# TTS 봇 담곰 프로젝트 

discord.py, edge-tts 라이브러리를 사용하여 입력 언어 감지로 6개국어에 대한 tts를 출력하는 디스코드 tts 봇

소스 파일 설명
### damgom_main.py
  봇 실행을 위한 Controller 모듈

### damgom_configure.py
  봇 객체 구성을 설정하는 Configuration, Initializer 모듈

### damgom_function.py
  봇의 명령어 처리, 데이터베이스 연동 등 전체적인 기능을 처리하는 Core Logic 모듈

### damgom_tokenizer.py
  봇 객체 구성을 위한 .env파일 내의 discord bot token, db 정보를 가져오는 Authentication 모듈

### damgom_audio.py
  봇 출력 값인 음성 데이터를 관리하는 Audio Control 모듈
