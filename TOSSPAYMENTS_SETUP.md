# 토스페이먼츠 연동 설정 가이드

## 1. 환경변수 설정 (.env)

프로젝트 루트의 `.env` 파일에 아래 변수들을 추가하세요.

```env
# 토스페이먼츠 API 키 (https://developers.tosspayments.com 에서 발급)
# 테스트용: test_ck_..., test_gsk_...
# 실서비스: live_ck_..., live_gsk_...
TOSSPAYMENTS_CLIENT_KEY=test_ck_D5GePWvyJnrK0W0k8eX3lmeaxYG5
TOSSPAYMENTS_SECRET_KEY=test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6
```

### 키 발급 방법
1. [토스페이먼츠 개발자센터](https://developers.tosspayments.com) 로그인
2. **내 개발정보** → **API 키** 메뉴
3. **클라이언트 키** → `.env`의 `TOSSPAYMENTS_CLIENT_KEY`에 입력
4. **시크릿 키** → `.env`의 `TOSSPAYMENTS_SECRET_KEY`에 입력

---

## 2. 결제 완료 후 유저 권한 업데이트 (선택)

결제가 성공하면 `app.py`의 `/success` 라우트에서 승인 API를 호출합니다.  
**유저를 무제한 이용권으로 업그레이드**하려면 아래 로직을 추가하세요.

### Supabase 사용 시

Supabase에서 `auth.users`의 `user_metadata`를 수정하려면 **서비스 롤 키(Service Role Key)**가 필요합니다.

1. `.env`에 추가:
```env
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

2. Supabase 대시보드 → **Project Settings** → **API** → `service_role` 키 복사

3. `app.py`의 `/success` 라우트에서 결제 성공 후 유저 업데이트:

```python
# 결제 성공 시 (res.status_code == 200) 블록 안에 추가
if supabase_admin and current_user_id:
    from datetime import datetime, timedelta
    if plan == "week":
        valid_until = (datetime.utcnow() + timedelta(days=7)).isoformat()
    elif plan == "month":
        valid_until = (datetime.utcnow() + timedelta(days=30)).isoformat()
    else:
        valid_until = None

    supabase_admin.auth.admin.update_user_by_id(
        current_user_id,
        {"user_metadata": {"is_paid": True, "plan_type": plan, "valid_until": valid_until}}
    )
```

**참고:** 결제 시점에 로그인한 사용자를 알아야 하므로:
- 로그인 사용자: `successUrl`에 `user_id`를 쿼리로 붙이거나, 세션/쿠키로 식별
- 비로그인: 이메일 입력 후 결제 → 결제 완료 시 링크 발송 등 별도 플로우 필요

---

## 3. 플랜별 금액 (코드에 하드코딩됨)

| 플랜   | 금액     | 비고     |
|--------|----------|----------|
| Free   | ₩0       | 기본     |
| A Week | ₩5,000   | 1주일    |
| A Month| ₩10,000  | 1개월    |
| Pro    | 준비중   | -        |

금액 변경 시 `app.py`의 `payment_success()` 검증 로직과 `pricing.html`의 `requestPayment()` 호출 부분을 함께 수정해야 합니다.

---

## 4. 테스트 결제

테스트 키 사용 시 **실제 결제가 발생하지 않습니다.**

- 테스트 카드: `1234-5678-9012-3456`
- 만료일: 임의의 미래 날짜 (예: 12/30)
- CVC: 3자리 숫자
- 비밀번호 앞 2자리: 임의

자세한 테스트 시나리오는 [토스페이먼츠 샌드박스](https://developers.tosspayments.com/sandbox) 참고.
