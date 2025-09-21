# news-read-agent

프로젝트 개요
- 이 저장소는 CrewAI 기반의 간단한 번역 에이전트(Crew) 예제를 포함합니다.
- main.py에서 CrewBase 데코레이터를 사용해 에이전트와 태스크를 정의하고, config/agents.yaml, config/tasks.yaml로 역할/목표/작업을 설정합니다.
- 실행 시 입력으로 sentence를 받아 번역 태스크(영→한)와 재번역 태스크(한→프)를 수행하도록 구성되어 있습니다.

기술 스택
- Python >= 3.11
- CrewAI (crewai[tools])
- python-dotenv (환경변수 로딩)
- uv (Python 프로젝트/의존성 관리)

프로젝트 구조
```
news-read-agent/
├─ main.py                 # Crew/Agent/Task 선언 및 실행 진입점
├─ pyproject.toml          # 프로젝트 메타데이터 및 의존성
├─ uv.lock                 # uv 잠금 파일
├─ config/
│  ├─ agents.yaml          # 에이전트 역할/목표/배경 설정
│  └─ tasks.yaml           # 태스크 설명/출력/에이전트 매핑
├─ .aiignore               # 분석/검색에서 제외할 파일/폴더 패턴(이 도구에서 존중)
├─ .gitignore              # Git 추적 제외 규칙
├─ .python-version         # 파이썬 버전 핀(예: 3.11)
└─ .venv/                  # 로컬 가상환경(uv sync 시 생성)
```

설치 및 실행
사전 요구사항
- Python 3.11 이상
- uv 설치(https://docs.astral.sh/uv/)

1) 의존성 설치
- 로컬 가상환경(.venv)을 생성하고 동기화합니다.
```
uv sync
```

2) 실행 방법
- 가상환경 활성화 후 직접 실행
```
source .venv/bin/activate
python main.py
```
- 혹은 uv로 일회성 실행
```
uv run python main.py
```

환경 변수(.env)
- main.py는 python-dotenv로 .env 파일을 자동 로드합니다.
- 사용 중인 LLM 제공자나 CrewAI 도구가 요구하는 키/설정이 있다면 .env에 정의하세요. 예시는 프로젝트 요구에 따라 상이할 수 있습니다(확실하지 않음).

설정 파일 요약
- config/agents.yaml
  - translator_agent: 한국어 설명으로 역할(role), 목표(goal), 배경(backstory)이 정의되어 있습니다.
- config/tasks.yaml
  - translator_task: 영어 문장 {sentence}를 한국어로 번역
  - retranslator_task: 한국어 문장 {sentence}를 프랑스어로 번역

예시 실행 입력
- main.py는 다음과 같이 kickoff를 호출합니다.
```
TranslaterCrew().assemble_crew().kickoff(inputs={"sentence": "Hello, how are you?"})
```
- sentence 값을 원하는 문장으로 바꾸어 실행할 수 있습니다.

개발 메모
- pyproject.toml 주요 의존성
  - crewai[tools]>=0.152.0
  - python-dotenv>=1.1.1
- 스크립트 항목([project.scripts])은 정의되어 있지 않으므로, 현재는 main.py 직접 실행 방식입니다.

테스트/품질 도구
- 이 저장소에는 테스트/린트 설정 파일이 포함되어 있지 않습니다(확실하지 않음). 필요 시 pytest/ruff/black 등을 추가하세요.

주의 사항
- .aiignore에 명시된 패턴(.DS_Store, *.log, *.tmp, dist/, build/, out/)은 이 도구의 분석/검색 단계에서 제외합니다.
- 민감정보가 포함된 환경 변수는 .env로 관리하고, 커밋되지 않도록 .gitignore를 유지하세요.

라이선스
- 라이선스 정보가 명시되어 있지 않습니다(확실하지 않음). 필요 시 LICENSE 파일을 추가하세요.