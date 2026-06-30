# Worklog

## 2026-06-27

### Context Review

- 프로젝트가 OWASP ZAP 기반 DAST 자동화 도구라는 점을 확인했다.
- 기존 구성은 PowerShell 스크립트, ZAP raw report, Markdown summary 중심이었다.
- `README`가 비어 있었고, 포트폴리오용 프로젝트 설명과 실행 흐름이 부족했다.
- `scanner/zap_custom_scan.py`는 정의되지 않은 함수가 많아 실행 불가 상태였다.

### Design Documentation

- `README`에 포트폴리오용 프로젝트 설계 문서를 추가했다.
- 핵심 방향을 다음과 같이 정리했다.
  - ZAP 스캔 실행
  - raw report 보존
  - normalized schema 생성
  - redaction 처리
  - Markdown 보고서 생성
  - CI/CD 보안 게이트 확장

### Phase 1 Implementation

- `scanner/zap_custom_scan.py`를 삭제했다.
- `scanner/run_dast.ps1`, `scanner/run_dast_api.ps1`를 삭제했다.
- Docker 기반 1차 파이프라인 파일을 추가했다.
  - `docker-compose.yml`
  - `Dockerfile`
  - `.dockerignore`
  - `.env.example`
  - `config/scan.example.yaml`
- Python reporter 파이프라인을 추가했다.
  - `scanner/models.py`
  - `scanner/normalize_zap.py`
  - `scanner/redact.py`
  - `scanner/report.py`
  - `scanner/pipeline.py`
- ZAP에서 취약점 발견으로 non-zero exit code가 나와도 raw JSON이 생성되면 reporter가 실행되도록 Compose command를 구성했다.
- `.gitignore`를 갱신해서 generated report와 `.env`가 Git에 들어가지 않도록 했다.

### LLM Removal

- 외부 LLM API 연동을 제거했다.
- `scanner/llm_report.py`를 삭제했다.
- 최종 Markdown 보고서는 `scanner/report.py`에서 로컬 규칙 기반으로 생성하도록 변경했다.
- `.env.example`, `docker-compose.yml`, `config/scan.example.yaml`, README에서 LLM 설정을 제거했다.

### Authenticated Scan

- 이미 발급받은 인증 헤더와 쿠키를 ZAP 요청에 주입하는 기능을 추가했다.
- `.env`에서 다음 값을 설정할 수 있다.
  - `AUTH_ENABLED`
  - `AUTH_HEADER_1_NAME`
  - `AUTH_HEADER_1_VALUE`
  - `AUTH_HEADER_2_NAME`
  - `AUTH_HEADER_2_VALUE`
  - `AUTH_HEADER_3_NAME`
  - `AUTH_HEADER_3_VALUE`
  - `AUTH_COOKIE`
- 이 기능은 로그인 자동화를 수행하지 않는다.
- 지원 범위는 Authorization Bearer token, API key header, CSRF header, custom header, Cookie header 주입이다.

### Documentation Added

- `IMPLEMENTATION_PHASE1.md`
  - 1차 구현 목표, 추가 파일, 실행 흐름, 환경변수, 설계 판단, 한계, 다음 단계 정리
- `zap_tutor.md`
  - OWASP ZAP 설명과 실습형 튜토리얼 문서 추가
  - DAST, Proxy, Spider, Passive Scan, Active Scan, Baseline Scan, API Scan, Authenticated Scan 설명

### Verified

- `docker compose config`로 Compose 문법을 확인했다.
- 기존 ZAP JSON 기준으로 reporter 파이프라인이 normalized, redacted, final report를 생성하는 것을 확인했다.
- redaction 정규식이 도메인을 JWT로 오탐하던 문제를 수정했다.

### Remaining Work

- OpenAPI scan 모드 추가
- scan id 또는 timestamp 기반 결과 디렉터리 분리
- YAML config 직접 로딩
- redaction 단위 테스트
- normalized schema 테스트
- 인증 주입이 실제 대상 요청에 적용되는지 테스트용 엔드포인트로 검증

