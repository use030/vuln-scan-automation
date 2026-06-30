# Automated DAST Report Pipeline

OWASP ZAP 기반의 자동화 취약점 점검 파이프라인입니다.

이 프로젝트는 URL을 입력받아 ZAP baseline scan을 실행하고, 원본 리포트를 정규화한 뒤, 민감정보를 마스킹하고, 사람이 읽을 수 있는 Markdown 보안 보고서를 생성합니다.

devsecops 프로세스의 보안 게이트 기능으로 삽입할 수 있습니다. 

## Usage

1. 환경 파일을 준비합니다.

```powershell
Copy-Item .env.example .env
```

2. `.env`에서 스캔 대상을 설정합니다.

```env
# baseline 또는 openapi
SCAN_MODE=baseline
TARGET_URL=https://example.com
OUTPUT_DIR=./reports
OPENAPI_DIR=./openapi
OPENAPI_FILE=openapi.json
OPENAPI_TARGET=
ZAP_MAX_DURATION=1
FAIL_ON=none
```

3. Docker Compose로 전체 파이프라인을 실행합니다.

```powershell
docker compose up --build
```

4. 결과 파일을 확인합니다.

```text
reports/raw/zap-report.json
reports/raw/zap-report.html
reports/normalized/normalized-report.json
reports/normalized/redacted-report.json
reports/final/security-report.md
```

보안 게이트처럼 사용하려면 `FAIL_ON`을 설정합니다.

```env
FAIL_ON=medium
```

`medium`으로 설정하면 Medium 이상 finding이 있을 때 reporter가 exit code `1`로 종료됩니다.

## Environment Variables

| Name | Default | Description |
|---|---|---|
| `SCAN_MODE` | `baseline` | `baseline` 또는 `openapi` |
| `TARGET_URL` | `https://example.com` | 스캔 대상 URL |
| `OUTPUT_DIR` | `./reports` | 결과물을 저장할 호스트 디렉터리 |
| `OPENAPI_DIR` | `./openapi` | 로컬 OpenAPI 파일이 있는 호스트 디렉터리 |
| `OPENAPI_FILE` | `openapi.json` | `OPENAPI_TARGET`이 비어 있을 때 사용할 OpenAPI 파일명 |
| `OPENAPI_TARGET` | empty | 직접 지정할 Swagger/OpenAPI URL 또는 컨테이너 내부 파일 경로 |
| `ZAP_MAX_DURATION` | `1` | ZAP spider 최대 실행 시간 |
| `FAIL_ON` | `none` | `none`, `low`, `medium`, `high` |
| `AUTH_ENABLED` | `false` | 인증 헤더/쿠키 주입 여부 |
| `AUTH_HEADER_1_NAME` | empty | 첫 번째 인증/커스텀 헤더 이름 |
| `AUTH_HEADER_1_VALUE` | empty | 첫 번째 인증/커스텀 헤더 값 |
| `AUTH_HEADER_2_NAME` | empty | 두 번째 인증/커스텀 헤더 이름 |
| `AUTH_HEADER_2_VALUE` | empty | 두 번째 인증/커스텀 헤더 값 |
| `AUTH_HEADER_3_NAME` | empty | 세 번째 인증/커스텀 헤더 이름 |
| `AUTH_HEADER_3_VALUE` | empty | 세 번째 인증/커스텀 헤더 값 |
| `AUTH_COOKIE` | empty | 요청에 주입할 Cookie header 값 |

## Scan Modes

### Baseline Scan

웹 URL을 빠르게 점검하는 기본 모드입니다.

```env
SCAN_MODE=baseline
TARGET_URL=http://host.docker.internal:8080
```

Baseline scan은 링크, `robots.txt`, `sitemap.xml`, HTML/JS에서 발견되는 URL을 중심으로 탐색합니다. REST API의 모든 하위 경로나 POST 요청을 자동으로 알지는 못합니다.

### OpenAPI Scan

Swagger/OpenAPI 명세를 기반으로 REST API 엔드포인트를 점검하는 모드입니다.

```env
SCAN_MODE=openapi
OPENAPI_TARGET=http://host.docker.internal:8080/v3/api-docs
TARGET_URL=http://host.docker.internal:8080
```

OpenAPI 문서에 `paths`, HTTP method, request body schema가 있으면 ZAP이 해당 API 요청을 생성해서 스캔할 수 있습니다.

로컬 OpenAPI 파일을 쓰려면 `./openapi/openapi.json`에 파일을 두고 다음처럼 설정합니다.

```env
SCAN_MODE=openapi
OPENAPI_DIR=./openapi
OPENAPI_FILE=openapi.json
OPENAPI_TARGET=
```

다른 디렉터리나 파일명을 쓰려면 `OPENAPI_DIR`와 `OPENAPI_FILE`만 바꾸면 됩니다.

```env
SCAN_MODE=openapi
OPENAPI_DIR=./docs/api-specs
OPENAPI_FILE=service-openapi.json
OPENAPI_TARGET=
```

URL이나 컨테이너 내부 경로를 직접 지정해야 하면 `OPENAPI_TARGET`을 설정합니다.

OpenAPI scan에서도 인증 헤더와 쿠키 주입은 동일하게 적용됩니다.

## Authenticated Scan

로그인이 필요한 서비스는 이미 발급받은 토큰이나 쿠키를 `.env`에 넣어서 ZAP 요청에 주입할 수 있습니다.

자동 로그인 기능은 지원하지 않습니다. 

```text
지원: 이미 발급받은 Authorization header, API key, CSRF header, Cookie 주입
지원 안함: 아이디/비밀번호 로그인, OAuth, MFA, CAPTCHA, 브라우저 자동 로그인
```

Bearer token 예시:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=Authorization
AUTH_HEADER_1_VALUE=Bearer your-access-token
AUTH_COOKIE=
```

API key 예시:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=X-API-Key
AUTH_HEADER_1_VALUE=your-api-key
AUTH_COOKIE=
```

Cookie session 예시:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=
AUTH_HEADER_1_VALUE=
AUTH_COOKIE=sessionid=abc123; csrftoken=def456
```

Bearer token과 CSRF header를 같이 쓰는 예시:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=Authorization
AUTH_HEADER_1_VALUE=Bearer your-access-token
AUTH_HEADER_2_NAME=X-CSRF-Token
AUTH_HEADER_2_VALUE=your-csrf-token
AUTH_COOKIE=sessionid=abc123
```

주의:

- `reports/raw/`에는 원본 ZAP 리포트가 저장되므로 토큰이 남을 수 있습니다.
- `reports/raw/`, `reports/normalized/`, `reports/final/`은 `.gitignore`에 포함되어 있습니다.

## Pipeline

```text
Target URL
  -> ZAP baseline scan
  -> raw JSON/HTML report
  -> normalized JSON
  -> redacted JSON
  -> final Markdown report
```

## Architecture

```text
docker-compose.yml
Dockerfile
scanner/
  pipeline.py
  normalize_zap.py
  redact.py
  report.py
  models.py
reports/
  raw/
  normalized/
  final/
openapi/
  openapi.json
config/
  scan.example.yaml
```



## Security Gate

`FAIL_ON`은 CI/CD에서 사용할 수 있는 보안 게이트 옵션입니다.
강도를 설정하면 보안 게이트가 활성화 됩니다. 

예:

```env
FAIL_ON=medium
```

이 경우 Medium 또는 High finding이 있으면 reporter가 실패합니다.

```text
Security gate failed: findings >= medium
```
