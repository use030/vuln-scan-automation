# OWASP ZAP Tutorial

이 문서는 OWASP ZAP을 처음 설명하고 실습하는 튜토리얼입니다. 목표는 ZAP을 단순히 실행하는 법이 아니라, DAST가 어떤 관점으로 웹 애플리케이션을 점검하는지 이해하는 것입니다.

## 1. OWASP ZAP이란?

OWASP ZAP은 웹 애플리케이션 보안 테스트를 자동화하는 오픈소스 도구입니다. 정식 이름은 Zed Attack Proxy입니다.

ZAP은 브라우저와 서버 사이에 프록시처럼 위치해서 HTTP 요청과 응답을 관찰하고, 보안상 위험한 패턴을 찾아냅니다. 또한 Spider, Ajax Spider, Passive Scan, Active Scan 같은 기능을 통해 애플리케이션의 공격 표면을 탐색하고 취약점을 점검합니다.

## 2. DAST란?

DAST는 Dynamic Application Security Testing의 약자입니다.

DAST는 실행 중인 애플리케이션을 외부에서 점검합니다. 코드를 직접 읽는 대신, 실제 HTTP 요청을 보내고 응답을 분석합니다.

```text
Scanner
  -> HTTP Request
  -> Running Web Application
  -> HTTP Response
  -> Response Analysis
```

장점:

- 실제 배포 환경에 가까운 상태를 점검할 수 있음
- HTTP 헤더, 쿠키, CORS, 인증 흐름 같은 런타임 동작 확인 가능
- 개발 언어나 프레임워크와 무관하게 사용 가능

한계:

- 코드 내부 로직을 직접 알 수 없음
- 로그인 이후 영역은 인증 설정 없이는 보기 어려움
- SPA는 일반 Spider만으로 탐색이 부족할 수 있음
- 자동화 결과에는 false positive가 포함될 수 있음

## 3. ZAP 핵심 개념

### Proxy

ZAP은 프록시로 동작할 수 있습니다. 브라우저의 프록시 설정을 ZAP으로 맞추면, 브라우저에서 발생하는 요청과 응답을 ZAP이 볼 수 있습니다.

```text
Browser
  -> ZAP Proxy
  -> Target Web Server
```

### Spider

Spider는 웹사이트의 링크를 따라가며 페이지를 탐색합니다.

예를 들어 `/`, `/login`, `/products`, `/robots.txt`, `/sitemap.xml` 같은 경로를 발견할 수 있습니다.

React, Vue, Angular 같은 SPA는 일반 Spider만으로 충분히 탐색되지 않을 수 있습니다. 이런 경우 Ajax Spider가 더 적합할 수 있습니다.

### Passive Scan

Passive Scan은 요청과 응답을 관찰만 합니다. 서버에 공격성 payload를 적극적으로 보내지 않습니다.

대표적으로 다음 항목을 확인합니다.

- CSP header 누락
- X-Frame-Options 누락
- X-Content-Type-Options 누락
- Cookie Secure/HttpOnly/SameSite 속성 누락
- CORS 과다 허용
- Cache-Control 설정 문제

운영 서비스에 비교적 안전하게 사용할 수 있는 방식입니다.

### Active Scan

Active Scan은 취약점을 찾기 위해 공격성 payload를 실제로 전송합니다.

예를 들어 SQL Injection, XSS, Command Injection 가능성을 확인하기 위해 다양한 입력값을 서버에 보낼 수 있습니다.

주의:

Active Scan은 운영 서비스에 함부로 실행하면 안 됩니다. 데이터 변경, 계정 잠금, 로그 폭증, 장애를 유발할 수 있습니다. 반드시 허가된 테스트 환경에서만 사용해야 합니다.

### Alert

ZAP이 발견한 보안 이슈를 Alert라고 부릅니다.

Alert에는 보통 다음 정보가 들어 있습니다.

- Alert name
- Risk
- Confidence
- CWE
- WASC
- Plugin ID
- Affected URL
- Evidence
- Description
- Solution

이 프로젝트에서는 이 Alert 정보를 정규화해서 사람이 읽기 좋은 보고서로 변환합니다.

## 4. Risk와 Confidence 이해하기

Risk는 문제가 실제로 악용되었을 때의 영향도를 의미합니다.

| Risk | Meaning |
|---|---|
| High | 심각한 보안 영향 가능 |
| Medium | 보안상 의미 있는 개선 필요 |
| Low | 낮은 위험이지만 개선 권장 |
| Informational | 참고 정보 |

Confidence는 ZAP이 해당 문제를 얼마나 확신하는지에 가깝습니다.

| Confidence | Meaning |
|---|---|
| High | 탐지 근거가 비교적 명확함 |
| Medium | 가능성이 있으나 확인 필요 |
| Low | false positive 가능성이 큼 |

좋은 보고서는 Risk만 보지 않습니다. Risk, Confidence, Evidence, Affected URL을 함께 봐야 합니다.

## 5. Baseline Scan

Baseline Scan은 ZAP Docker 이미지에서 제공하는 기본 스캔 방식입니다.

특징:

- Spider 실행
- Passive Scan 실행
- HTML/JSON 리포트 생성
- 운영 서비스에 상대적으로 안전
- 빠르게 보안 헤더와 기본 설정 문제를 찾는 데 적합

예시:

```powershell
docker run --rm `
  -v ${PWD}/reports:/zap/wrk `
  ghcr.io/zaproxy/zaproxy:stable `
  zap-baseline.py `
  -t https://example.com `
  -r zap-baseline-report.html `
  -J zap-baseline-report.json
```

이 프로젝트에서는 이 과정을 `SCAN_MODE=baseline`과 `docker-compose.yml`로 자동화합니다.

## 6. API Scan

API Scan은 OpenAPI 명세를 바탕으로 API 엔드포인트를 점검합니다.

Baseline Scan은 링크를 따라가며 페이지를 찾지만, API 서버는 링크 구조가 없을 수 있습니다. 이런 경우 OpenAPI 문서가 있으면 ZAP이 엔드포인트를 더 정확히 찾을 수 있습니다.

예시:

```powershell
docker run --rm `
  -v ${PWD}/reports:/zap/wrk `
  ghcr.io/zaproxy/zaproxy:stable `
  zap-api-scan.py `
  -t https://example.com/openapi.json `
  -f openapi `
  -r zap-api-report.html `
  -J zap-api-report.json
```

이 프로젝트에서는 다음처럼 설정합니다.

```env
SCAN_MODE=openapi
OPENAPI_TARGET=http://host.docker.internal:8080/v3/api-docs
TARGET_URL=http://host.docker.internal:8080
```

OpenAPI 문서에 request body schema가 있으면 POST, PUT 같은 요청도 기본적으로 생성할 수 있습니다. 다만 비즈니스적으로 유효한 값이 필요하다면 OpenAPI 문서에 `example`을 넣는 것이 좋습니다.

## 7. Authenticated Scan

인증이 필요한 서비스는 로그인하지 않은 상태로 스캔하면 중요한 영역을 거의 볼 수 없습니다.

예를 들어 다음 영역은 인증 없이는 탐색되지 않을 수 있습니다.

- 마이페이지
- 관리자 페이지
- 결제 내역
- 사용자별 API
- 글 작성/수정/삭제 API

인증 스캔에서는 쿠키, 세션, Authorization header 등을 ZAP에 전달해야 합니다.

주의할 점:

- 인증 토큰은 리포트에 남을 수 있음
- 최종 보고서 생성 전에 redaction 필요
- 테스트 계정을 사용해야 함
- 권한별 계정을 나누어 테스트해야 함

## 8. 이 프로젝트에서 ZAP을 사용하는 방식

현재 구현은 다음 흐름을 사용합니다.

```text
docker compose up --build
  -> zap service
     -> zap-baseline.py 또는 zap-api-scan.py 실행
     -> reports/raw/zap-report.json 생성
  -> reporter service
     -> JSON 정규화
     -> 민감정보 마스킹
     -> Markdown 보고서 생성
```

ZAP은 취약점을 발견하면 non-zero exit code를 반환할 수 있습니다. 이 프로젝트에서는 JSON 리포트가 생성되었으면 ZAP 실행 자체는 성공으로 보고, 최종 실패 여부는 reporter의 `FAIL_ON` 정책으로 판단합니다.

## 9. 실습 1: Baseline Scan 실행

`.env.example`을 참고해서 `.env`를 준비합니다.

```env
TARGET_URL=https://example.com
OUTPUT_DIR=./reports
OPENAPI_TARGET=
ZAP_MAX_DURATION=1
FAIL_ON=none
```

실행:

```powershell
docker compose up --build
```

생성 결과:

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

## 10. 실습 2: 보안 게이트 설정

`FAIL_ON` 값을 설정하면 특정 심각도 이상의 finding이 있을 때 reporter가 실패합니다.

예시:

```env
FAIL_ON=medium
```

의미:

```text
Medium 이상 finding이 하나라도 있으면 exit code 1 반환
```

CI/CD에서는 이 값을 사용해서 보안 기준을 강제할 수 있습니다.

## 11. 실습 3: OpenAPI Scan 실행

REST API를 스캔하려면 Swagger/OpenAPI 명세를 입력으로 사용하는 것이 좋습니다.

```env
SCAN_MODE=openapi
OPENAPI_TARGET=http://host.docker.internal:8080/v3/api-docs
TARGET_URL=http://host.docker.internal:8080
```

실행:

```powershell
docker compose up --build
```

로컬 파일을 사용할 경우:

```text
openapi/openapi.json
```

파일을 만든 뒤 다음처럼 설정합니다.

```env
SCAN_MODE=openapi
OPENAPI_DIR=./openapi
OPENAPI_FILE=openapi.json
OPENAPI_TARGET=
```

다른 디렉터리를 쓰려면 `OPENAPI_DIR`를 바꾸고, 다른 파일명을 쓰려면 `OPENAPI_FILE`을 바꿉니다.

OpenAPI scan은 API path와 method를 문서에서 읽기 때문에 baseline scan보다 REST API 점검에 적합합니다.

## 12. 실습 4: 인증 헤더 또는 쿠키 주입

로그인이 필요한 서비스는 이미 발급받은 토큰이나 쿠키를 `.env`에 넣어서 스캔할 수 있습니다.

이 프로젝트는 로그인을 대신 수행하지 않습니다. 브라우저나 API 클라이언트에서 미리 발급받은 값을 ZAP 요청에 붙이는 방식입니다.

Bearer token 예시:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=Authorization
AUTH_HEADER_1_VALUE=Bearer your-access-token
```

Cookie 예시:

```env
AUTH_ENABLED=true
AUTH_COOKIE=sessionid=abc123; csrftoken=def456
```

CSRF header와 Cookie를 같이 쓰는 예시:

```env
AUTH_ENABLED=true
AUTH_HEADER_1_NAME=X-CSRF-Token
AUTH_HEADER_1_VALUE=your-csrf-token
AUTH_COOKIE=sessionid=abc123; csrftoken=your-csrf-token
```

주의:

- `.env`에는 실제 인증정보가 들어가므로 Git에 커밋하면 안 됩니다.
- `reports/raw/`에는 원본 리포트가 저장되므로 인증정보가 남을 수 있습니다.
- 이 방식은 OAuth, MFA, CAPTCHA, 브라우저 로그인 자동화를 지원하지 않습니다.

## 13. 결과 해석 예시

예를 들어 ZAP이 다음 alert를 발견했다고 가정합니다.

```text
Content Security Policy Header Not Set
Risk: Medium
CWE: 693
Affected URL: https://example.com/
```

이 의미는 응답에 CSP 헤더가 없다는 뜻입니다. CSP는 XSS나 데이터 주입 공격의 영향을 줄이는 방어 계층입니다.

개선 방향:

```http
Content-Security-Policy: default-src 'self'; frame-ancestors 'none';
```

단, 실제 CSP는 서비스에서 사용하는 script, style, image, font, API origin을 고려해서 점진적으로 설계해야 합니다.

## 14. 자주 나오는 Alert

| Alert | Meaning | Typical Fix |
|---|---|---|
| CSP Header Not Set | CSP 헤더 없음 | `Content-Security-Policy` 추가 |
| Missing Anti-clickjacking Header | clickjacking 방어 없음 | `frame-ancestors` 또는 `X-Frame-Options` |
| X-Content-Type-Options Missing | MIME sniffing 방어 없음 | `X-Content-Type-Options: nosniff` |
| Cross-Domain Misconfiguration | CORS 과다 허용 | `Access-Control-Allow-Origin` 제한 |
| Cookie without HttpOnly | JS에서 쿠키 접근 가능 | `HttpOnly` 설정 |
| Cookie without Secure | HTTPS에서만 쿠키 전송 제한 없음 | `Secure` 설정 |

## 15. 좋은 ZAP 자동화의 기준

좋은 자동화는 단순히 리포트를 생성하지 않습니다.

반드시 갖춰야 할 요소:

- 원본 리포트 보존
- 정규화된 finding schema
- 민감정보 마스킹
- evidence 보존
- false positive 검토 가능성
- severity threshold 기반 실패 처리
- CI/CD 연동 가능성
- 인증 스캔 확장 가능성

## 16. 주의사항

ZAP은 강력한 보안 테스트 도구입니다.

다음 원칙을 지켜야 합니다.

1. 본인 소유 또는 명시적으로 허가받은 대상만 스캔합니다.
2. 운영 서비스에는 active scan을 함부로 실행하지 않습니다.
3. 인증 토큰과 쿠키가 리포트에 남지 않도록 관리합니다.
4. 리포트에는 민감한 URL, 내부 IP, 사용자 정보가 포함될 수 있습니다.
5. 자동화 결과를 맹신하지 말고 evidence를 확인합니다.
