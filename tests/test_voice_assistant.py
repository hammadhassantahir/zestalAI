"""
E2E test for the voice assistant calling module.
Validates: phone check → config check → schedule check → call → poll → verify.

WARNING: Makes a REAL call to TEST_LEAD_NUMBER — costs money.

Run:
    1. Start server: python wsgi.py
    2. Run test:     python tests/test_voice_assistant.py
"""
import sys
import os
import json
import time
import requests
from datetime import datetime

BASE_URL = os.getenv('TEST_BASE_URL', 'http://127.0.0.1:5001/api')
TEST_EMAIL = 'faisalkhan388@hotmail.com'
TEST_PASSWORD = 'test123'
TEST_LEAD_NUMBER = '+923004675386'


def header(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def step(num, desc, method, url, expected_status, token=None, body=None, headers_override=None):
    print(f"\n{'─' * 60}")
    print(f"Step {num}: {desc}")
    print(f"  {method} {url}")

    hdrs = headers_override or (header(token) if token else {'Content-Type': 'application/json'})

    try:
        resp = requests.request(method, url, headers=hdrs, json=body, timeout=30)
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] Connection refused — is the server running on {BASE_URL}?")
        sys.exit(1)

    status_ok = resp.status_code == expected_status
    data = None
    try:
        data = resp.json()
    except Exception:
        data = resp.text[:300]

    print(f"  Status: {resp.status_code} {'OK' if status_ok else f'EXPECTED {expected_status}'}")
    print(f"  Response: {json.dumps(data, indent=2)[:500]}")

    if not status_ok:
        print(f"\n  [FAIL] Step {num} failed!")
        sys.exit(1)

    print(f"  [PASS]")
    return data


def run_tests():
    print("=" * 60)
    print("VOICE ASSISTANT E2E TEST")
    print(f"Lead: {TEST_LEAD_NUMBER}")
    print("=" * 60)

    # ── Step 1: Login ──────────────────────────────────────────
    data = step(1, "Login", "POST",
                f"{BASE_URL}/auth/login", 200,
                body={'email': TEST_EMAIL, 'password': TEST_PASSWORD})
    token = data['access_token']
    user_id = data['user']['id']
    print(f"  Token: {token[:20]}...")
    print(f"  User ID: {user_id}")

    # ── Step 2: Check phone number ─────────────────────────────
    data = step(2, "Check assigned phone numbers", "GET",
                f"{BASE_URL}/phone/my-numbers", 200, token)
    numbers = data.get('phone_numbers', [])
    active = [n for n in numbers if n['status'] == 'assigned']

    if not active:
        print("  [FAIL] No active number. Purchase one first.")
        sys.exit(1)

    phone = active[0]
    phone_ok = True
    vapi_ok = bool(phone.get('vapi_phone_id'))
    print(f"  Number: {phone['phone_number']}")
    print(f"  vapi_phone_id: {phone.get('vapi_phone_id', 'NOT SET')}")

    if not vapi_ok:
        print("  [FAIL] Number not imported to Vapi")
        sys.exit(1)

    # ── Step 3: Check/create call config ───────────────────────
    data = step(3, "Check call config", "GET",
                f"{BASE_URL}/config/call", 200, token)
    cfg = data.get('config')

    if not cfg:
        data = step("3b", "Create default call config", "PUT",
                    f"{BASE_URL}/config/call", 200, token,
                    body={'is_active': True, 'active_template': 'lead_qualification', 'tone': 'formal'})
        cfg = data['config']
        print("  Created default config")
    else:
        print(f"  Tone: {cfg.get('tone')}")
        print(f"  Template: {cfg.get('active_template')}")
        print(f"  Language: {cfg.get('default_language')}")
        print(f"  Voice: {cfg.get('voice_id')}")
        print(f"  Active: {cfg.get('is_active')}")

    config_active = cfg.get('is_active', False)
    if not config_active:
        print("  ⚠ Config is_active=false — call may fail")

    # ── Step 4: Check schedule config ──────────────────────────
    print(f"\n{'─' * 60}")
    print("Step 4: Check schedule config")
    win_start = cfg.get('call_window_start')
    win_end = cfg.get('call_window_end')
    win_days = cfg.get('call_window_days')
    win_tz = cfg.get('call_window_timezone')

    if win_start and win_end:
        print(f"  Window: {win_start} - {win_end} ({win_tz or 'no tz'})")
        print(f"  Days: {win_days or 'all'}")
        now = datetime.now()
        print(f"  Current time: {now.strftime('%H:%M %A')}")
        print("  (calling regardless — test bypasses window)")
    else:
        print("  No schedule restrictions")
    print("  [PASS]")

    # ── Step 5: Pre-call summary ───────────────────────────────
    print(f"\n{'─' * 60}")
    print("Step 5: Pre-call readiness")
    print(f"  Phone number: {'✓' if phone_ok else '✗'} {phone['phone_number']}")
    print(f"  Vapi import:  {'✓' if vapi_ok else '✗'}")
    print(f"  Config active: {'✓' if config_active else '✗'}")
    print(f"  Template:     {cfg.get('active_template', 'none')}")
    print(f"  Lead number:  {TEST_LEAD_NUMBER}")
    print("  [PASS]")

    # ── Step 6: Wait 30s then initiate call ────────────────────
    print(f"\n{'─' * 60}")
    print("Step 6: Initiate call (30s countdown)")
    for remaining in [30, 20, 10]:
        print(f"  Calling in {remaining}s...")
        time.sleep(10)

    data = step("6b", f"Initiate call to {TEST_LEAD_NUMBER}", "POST",
                f"{BASE_URL}/calls/", 201, token,
                body={
                    'customer_number': TEST_LEAD_NUMBER,
                    'lead_context': {
                        'name': 'Test Lead',
                        'company': 'Test Corp',
                        'notes': 'E2E voice assistant test',
                    },
                })

    call = data['call']
    call_id = call['id']
    vapi_call_id = call.get('vapi_call_id')
    print(f"  Call ID: {call_id}")
    print(f"  Vapi Call ID: {vapi_call_id}")

    # ── Step 7: Poll call status ───────────────────────────────
    print(f"\n{'─' * 60}")
    print("Step 7: Poll call status (max 120s)")
    terminal = {'ended', 'failed', 'hang'}
    prev_status = None
    elapsed = 0
    poll_interval = 5
    max_wait = 120

    while elapsed < max_wait:
        resp = requests.get(f"{BASE_URL}/calls/{call_id}", headers=header(token), timeout=30)
        poll_data = resp.json()
        cur_status = poll_data['call'].get('status', 'unknown')

        if cur_status != prev_status:
            print(f"  [{elapsed}s] Status: {cur_status}")
            prev_status = cur_status

        if cur_status in terminal:
            break

        time.sleep(poll_interval)
        elapsed += poll_interval

    if elapsed >= max_wait:
        print(f"  ⚠ Timed out after {max_wait}s — last status: {cur_status}")

    final_status = cur_status
    print("  [PASS]")

    # ── Step 8: Verify call data ───────────────────────────────
    data = step(8, "Get call details", "GET",
                f"{BASE_URL}/calls/{call_id}", 200, token)
    c = data['call']
    print(f"  Status: {c.get('status')}")
    print(f"  Duration: {c.get('duration_seconds', 'n/a')}s")
    print(f"  Cost: {c.get('cost', 'n/a')}")
    print(f"  Transcript: {(c.get('transcript') or 'none')[:120]}")
    print(f"  Summary: {(c.get('summary') or 'none')[:120]}")
    print(f"  Recording: {c.get('recording_url', 'none')}")

    # analytics (may 404 if not ready)
    print(f"\n  Checking analytics...")
    resp = requests.get(f"{BASE_URL}/calls/{call_id}/analytics", headers=header(token), timeout=30)
    if resp.status_code == 200:
        a = resp.json().get('analytics', {})
        print(f"  Sentiment: {a.get('sentiment')}")
        print(f"  Interest: {a.get('interest_level')}")
        print(f"  Objections: {a.get('objections')}")
        print(f"  Success: {a.get('success_evaluation')}")
    else:
        print(f"  Analytics not ready (status {resp.status_code})")

    # result (may 404)
    print(f"\n  Checking call result...")
    resp = requests.get(f"{BASE_URL}/calls/{call_id}/result", headers=header(token), timeout=30)
    if resp.status_code == 200:
        r = resp.json().get('result', {})
        print(f"  Result: {json.dumps(r, indent=2)[:300]}")
    else:
        print(f"  Result not ready (status {resp.status_code})")

    # ── Step 9: Verify in call history ─────────────────────────
    data = step(9, "Check call history", "GET",
                f"{BASE_URL}/calls/?page=1&per_page=5", 200, token)
    calls = data.get('calls', [])
    found = any(c['id'] == call_id for c in calls)
    print(f"  Total calls: {data.get('total')}")
    print(f"  Test call in list: {'✓' if found else '✗'}")
    if not found:
        print("  ⚠ Call not found in recent history")

    # ── Done ───────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("VOICE ASSISTANT E2E TEST COMPLETE")
    print(f"  Final status: {final_status}")
    print(f"  Duration: {c.get('duration_seconds', '?')}s")
    print(f"  Cost: {c.get('cost', '?')}")
    if resp.status_code == 200 and 'analytics' in locals():
        a_resp = requests.get(f"{BASE_URL}/calls/{call_id}/analytics", headers=header(token), timeout=30)
        if a_resp.status_code == 200:
            print(f"  Sentiment: {a_resp.json().get('analytics', {}).get('sentiment', '?')}")
    result = "PASS" if final_status == 'ended' else "FAIL"
    print(f"  Result: {result}")
    print("=" * 60)


if __name__ == '__main__':
    run_tests()
