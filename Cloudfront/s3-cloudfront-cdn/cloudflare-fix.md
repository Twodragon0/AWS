# Cloudflare + CloudFront 연결 문제 해결

## 🔍 **현재 상황**
- ✅ DNS 설정: 정상 (Cloudflare IP로 해석)
- ✅ CloudFront: 직접 접속 시 정상 작동
- ❌ s3.2twodragon.com: 403 오류

## 🚨 **문제 원인**
Cloudflare Proxy가 CloudFront로 요청을 보낼 때 **Host Header** 문제

## 🛠️ **해결 방법**

### 방법 1: Cloudflare Page Rules 추가

1. **Cloudflare 대시보드** → **Rules** → **Page Rules**
2. **Create Page Rule** 클릭
3. 다음과 같이 설정:

```
URL: s3.2twodragon.com/*
Settings:
- Host Header Override: d4gy2qwg5fhz0.cloudfront.net
```

### 방법 2: Cloudflare Transform Rules (권장)

1. **Cloudflare 대시보드** → **Rules** → **Transform Rules**
2. **Modify Request Header** 탭
3. **Create rule** 클릭
4. 설정:

```
Rule name: CloudFront Host Fix
When incoming requests match: Hostname equals s3.2twodragon.com
Then: Set static → Host → d4gy2qwg5fhz0.cloudfront.net
```

### 방법 3: SSL/TLS 모드 확인

1. **SSL/TLS** → **Overview**
2. **Encryption mode**를 **Full (strict)** 로 설정

### 방법 4: Origin Rules (최신 방법)

1. **Rules** → **Origin Rules**
2. **Create rule**
3. 설정:

```
Rule name: S3 CloudFront Origin
When incoming requests match: Hostname equals s3.2twodragon.com
Then:
- Host Header: Override to d4gy2qwg5fhz0.cloudfront.net
- Destination address: Override to d4gy2qwg5fhz0.cloudfront.net
```

## 🎯 **권장 순서**

1. **SSL/TLS 모드** → **Full (strict)** 설정
2. **Origin Rules** 또는 **Transform Rules** 추가
3. 5분 대기 후 테스트

## 🧪 **테스트 방법**

```bash
# 1. 직접 CloudFront 테스트 (이미 작동 중)
curl -I https://d4gy2qwg5fhz0.cloudfront.net

# 2. Cloudflare 경유 테스트
curl -I https://s3.2twodragon.com

# 3. Host Header 확인
curl -H "Host: d4gy2qwg5fhz0.cloudfront.net" https://s3.2twodragon.com
``` 