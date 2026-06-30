# Phase 1 Implementation Notes

이 문서는 1차 구현 범위를 정리합니다.

## 1. Goal

1차 목표는 Docker 명령 한 번으로 다음 흐름을 실행하는 것입니다.

```text
Target URL 입력
  -> OWASP ZAP baseline 또는 OpenAPI scan
  -> optional auth header/cookie injection
  -> raw JSON/HTML report 저장
  -> Python normalizer 실행
  -> redaction 처리
  -> final Markdown report 생성
```

최종 Markdown 보고서는 외부 API 없이 로컬 Python 코드로 생성합니다.

## 2. Added Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | ZAP scan service와 Python reporter service 실행 |
| `Dockerfile` | reporter 컨테이너 이미지 정의 |
| `.env.example` | 실행 환경변수 예시 |
| `.dockerignore` | Docker build context 정리 |
| `config/scan.example.yaml` | 향후 config 기반 실행을 위한 예시 |
| `scanner/models.py` | normalized report dataclass 모델 |
| `scanner/normalize_zap.py` | ZAP JSON 정규화 |
| `scanner/redact.py` | 민감정보 마스킹 |
| `scanner/report.py` | Markdown 보고서 생성 |
| `scanner/pipeline.py` | reporter 전체 파이프라인 엔트리포인트 |

삭제한 파일:

| File | Reason |
|---|---|
| `scanner/zap_custom_scan.py` | 정의되지 않은 함수가 많아 실행 불가 상태였음 |
| `scanner/run_dast.ps1` | Compose 기반 실행으로 대체됨 |
| `scanner/run_dast_api.ps1` | Compose 기반 실행으로 대체됨 |
| `scanner/llm_report.py` | LLM 연동 제거 후 로컬 보고서 생성기로 대체됨 |

## 3. Runtime Flow

```text
docker compose up --build
```

Compose는 두 서비스를 실행합니다.

```text
zap
  image: ghcr.io/zaproxy/zaproxy:stable
  output: reports/raw/zap-report.json
          reports/raw/zap-report.html

reporter
  image: local Python image
  input: reports/raw/zap-report.json
  output: reports/normalized/normalized-report.json
          reports/normalized/redacted-report.json
          reports/final/security-report.md
```

## 4. Environment Variables

| Name | Default | Description |
|---|---|---|
| `SCAN_MODE` | `baseline` | `baseline` 또는 `openapi` |
| `TARGET_URL` | `https://example.com` | 스캔 대상 URL |
| `OUTPUT_DIR` | `./reports` | 결과물을 저장할 호스트 디렉터리 |
| `OPENAPI_DIR` | `./openapi` | 로컬 OpenAPI 파일이 있는 호스트 디렉터리 |
| `OPENAPI_FILE` | `openapi.json` | `OPENAPI_TARGET`이 비어 있을 때 사용할 OpenAPI 파일명 |
| `OPENAPI_TARGET` | empty | 직접 지정할 Swagger/OpenAPI URL 또는 컨테이너 내부 파일 경로 |
| `ZAP_MAX_DURATION` | `1` | ZAP spider 최대 실행 시간 |
| `FAIL_ON` | `none` | `low`, `medium`, `high` 기준 보안 게이트 |
| `AUTH_ENABLED` | `false` | 인증 헤더/쿠키 주입 여부 |
| `AUTH_HEADER_1_NAME` | empty | 첫 번째 인증/커스텀 헤더 이름 |
| `AUTH_HEADER_1_VALUE` | empty | 첫 번째 인증/커스텀 헤더 값 |
| `AUTH_HEADER_2_NAME` | empty | 두 번째 인증/커스텀 헤더 이름 |
| `AUTH_HEADER_2_VALUE` | empty | 두 번째 인증/커스텀 헤더 값 |
| `AUTH_HEADER_3_NAME` | empty | 세 번째 인증/커스텀 헤더 이름 |
| `AUTH_HEADER_3_VALUE` | empty | 세 번째 인증/커스텀 헤더 값 |
| `AUTH_COOKIE` | empty | 요청에 주입할 Cookie header 값 |

## 5. Design Decisions

### ZAP exit code handling

ZAP baseline scan은 경고나 취약점이 발견되면 non-zero exit code를 반환할 수 있습니다. 이 프로젝트에서는 취약점 발견을 스캔 실패로 보지 않습니다.

따라서 ZAP 컨테이너는 JSON 리포트가 정상 생성되었으면 성공으로 종료합니다. 실제 실패 여부는 reporter 단계에서 `FAIL_ON` 기준으로 판단합니다.

### Local Markdown report

외부 LLM API 의존성을 제거하고, 최종 Markdown 보고서는 로컬 Python 코드로 생성합니다.

이 방식의 장점:

- API 키가 필요 없음
- 요금/쿼터/rate limit 문제가 없음
- 같은 입력에 대해 같은 구조의 보고서를 생성함
- 포트폴리오 사용자가 바로 실행 가능함

### Static authenticated scan

인증이 필요한 서비스는 이미 발급받은 header 또는 cookie를 ZAP 요청에 주입할 수 있습니다.

지원 범위:

- Authorization Bearer token
- API key header
- CSRF header
- custom header
- Cookie header

지원하지 않는 범위:

- 아이디/비밀번호 로그인 자동화
- OAuth redirect
- MFA/OTP
- CAPTCHA
- 브라우저 자동 로그인

예:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=Authorization
AUTH_HEADER_1_VALUE=Bearer your-access-token
AUTH_COOKIE=sessionid=abc123
```

### OpenAPI scan mode

REST API는 baseline scan만으로 엔드포인트와 POST body를 충분히 발견하기 어렵습니다. 이를 보완하기 위해 `SCAN_MODE=openapi`를 지원합니다.

예:

```env
SCAN_MODE=openapi
OPENAPI_TARGET=http://host.docker.internal:8080/v3/api-docs
TARGET_URL=http://host.docker.internal:8080
```

OpenAPI 문서에 path, method, request body schema가 있으면 ZAP API Scan이 이를 기반으로 API 요청을 생성합니다.

로컬 파일을 쓰려면 `./openapi/openapi.json`에 파일을 두고 다음처럼 지정합니다.

```env
SCAN_MODE=openapi
OPENAPI_DIR=./openapi
OPENAPI_FILE=openapi.json
OPENAPI_TARGET=
```

다른 호스트 디렉터리나 파일명을 사용할 경우 `OPENAPI_DIR`와 `OPENAPI_FILE`을 바꿉니다. `OPENAPI_TARGET`을 비워두면 컨테이너 내부 경로 `/zap/openapi/${OPENAPI_FILE}`이 자동으로 사용됩니다.

### Redaction before final report

최종 보고서는 redacted report를 기반으로 생성합니다. 원본 ZAP JSON에는 토큰, 쿠키, 내부 IP, 이메일 같은 민감정보가 포함될 수 있기 때문입니다.

마스킹 대상:

- Authorization header
- Cookie
- JWT
- API key
- access token
- refresh token
- session id
- email
- phone number
- internal IP

## 6. Current Limitations

1차 구현은 baseline scan에 집중합니다.

아직 포함하지 않은 기능:

- OpenAPI scan 고도화
- 로그인 자동화 기반 authenticated scan
- Ajax Spider
- active scan
- config YAML 직접 로딩
- 테스트 코드
- scan id 기반 실행 디렉터리 분리

## 7. Expected Outputs

```text
reports/
  raw/
    zap-report.html
    zap-report.json
  normalized/
    normalized-report.json
    redacted-report.json
  final/
    security-report.md
```

## 8. Next Step

2차 구현에서는 다음 항목을 우선합니다.

1. scan id 또는 timestamp 기반 결과 디렉터리 분리
2. YAML config 로딩
3. redaction 단위 테스트
4. normalized schema 테스트
5. OpenAPI request example 품질 개선
6. README 실행 예시 보강
