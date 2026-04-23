import os
import requests
from datetime import datetime, timedelta

# 환경 변수
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://bzwgvqwroyqqrhvkgjoq.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6d2d2cXdyb3lxcXJodmtnam9xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5MTY4MDcsImV4cCI6MjA5MjQ5MjgwN30.N6A2zLF3jpajdnsHmCEpMvnvTjHUsp1PdgfpVuIDlPs')

TASK_RULES = {
    '안건심사': [
        {'label': '발의문 제출 마감 확인', 'base': '회기시작', 'offset': -10},
        {'label': '입법예고 시작', 'base': '회기시작', 'offset': -10},
        {'label': '검토보고서 초안 작성 → 전문위원 전달', 'base': '상임위', 'offset': -5},
        {'label': '회의 진행 시나리오 작성 완료', 'base': '상임위', 'offset': -3},
        {'label': '오늘의 의사일정 작성 완료', 'base': '상임위', 'offset': -3},
        {'label': '사무보고서 작성 완료', 'base': '상임위', 'offset': -3},
        {'label': '제안설명 시나리오 작성 (의원발의)', 'base': '상임위', 'offset': -3, '조건': '의원발의'},
        {'label': '전문위원 검토보고서 최종 확정', 'base': '상임위', 'offset': -2},
        {'label': '단톡방 — 검토보고서 + 의사일정 + 회의 안내 송부', 'base': '상임위', 'offset': -2},
        {'label': '출력 — 검토보고서 10부, 시나리오 4부, 의사일정 13부 등', 'base': '상임위', 'offset': -2},
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)', 'base': '상임위', 'offset': 0, '시각': '아침'},
        {'label': '결과보고 공문 → 운영위 담당자 송부', 'base': '상임위', 'offset': 0, '시각': '종료후'},
        {'label': '심사보고서 + 시나리오 작성 완료', 'base': '2차본회의', 'offset': -2},
    ],
    '추경심사': [
        {'label': '추경 예산서 회부 확인', 'base': '회기시작', 'offset': -10},
        {'label': '검토보고서 초안 작성(이호조 참고)', 'base': '상임위', 'offset': -5},
        {'label': '단톡방 — 검토보고서 + 의사일정 + 회의 안내 송부', 'base': '상임위', 'offset': -2},
        {'label': '계수조정 시나리오 + 목록 준비 완료', 'base': '상임위', 'offset': -2},
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)', 'base': '상임위', 'offset': 0, '시각': '아침'},
    ],
    '업무보고': [
        {'label': '회의 시나리오/의사일정/사무보고서 작성', 'base': '상임위', 'offset': -3},
        {'label': '단톡방 — 의사일정 + 회의 안내 송부', 'base': '상임위', 'offset': -2},
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)', 'base': '상임위', 'offset': 0, '시각': '아침'},
    ],
    '행감': [
        {'label': '행정사무감사 시작 준비 완료', 'base': '상임위', 'offset': -3},
        {'label': '단톡방 — 의사일정 + 행감 일정 안내 송부', 'base': '상임위', 'offset': -2},
        {'label': '📱 행감 진행 안내 문자 발송 (단톡방)', 'base': '상임위', 'offset': 0, '시각': '아침'},
    ],
    '본예산심사': [
        {'label': '검토보고서 초안 작성(예산서 참고)', 'base': '상임위', 'offset': -5},
        {'label': '단톡방 — 검토보고서 + 의사일정 + 회의 안내 송부', 'base': '상임위', 'offset': -2},
        {'label': '출력 — 검토보고서/시나리오/페이지목록 등', 'base': '상임위', 'offset': -2},
        {'label': '계수조정 시나리오 + 목록 준비', 'base': '상임위', 'offset': -2},
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)', 'base': '상임위', 'offset': 0, '시각': '아침'},
    ],
}


def get_dantalk_message(msg_type, 상임위일, 회기명, 회기유형, 차수):
    date_str = 상임위일.strftime('%y.%-m.%-d.')
    day_map = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}
    day_str = day_map[상임위일.weekday()]
    차수_str = f"제{차수}차 " if 차수 else ""

    if msg_type == 'D-2':
        if '행감' in 회기유형:
            msg = (
                f"📢 {회기명}\n"
                f"      <b>{차수_str}행정사무감사 실시 안내</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"• 일시: {date_str}({day_str}) 10:00\n"
                f"• 장소: 도시위원회 회의실\n"
                f"• 안건: {회기유형}\n\n"
                f" ⭐ 준비사항:\n"
                f"  - 행정사무감사 자료집\n"
                f"  - 요구자료 목록 및 답변서\n\n"
                f"위원님들의 심도 있는 감사를 부탁드립니다."
            )
        else:
            msg = (
                f"📢 {회기명}\n"
                f"      <b>{차수_str}도시위원회 일정 알림</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"• 일시: {date_str}({day_str}) 10:00\n"
                f"• 안건: {회기유형}\n\n"
                f" ⭐ 준비사항:\n"
                f"  - 검토보고서\n"
                f"  - 오늘의 의사일정"
            )
            if any(x in 회기유형 for x in ['예산', '추경']):
                msg += "\n  - 사업명세서\n  - 사업설명서"
            msg += "\n\n붙임: 오늘의 의사일정, 검토보고서"
        return msg

    if msg_type == 'D-0':
        title_str = f"{차수_str}행정사무감사" if '행감' in 회기유형 else f"{차수_str}도시위원회 회의"
        return (
            f"🔔 오늘({date_str}) {title_str} 안내\n\n"
            f"위원님, 안녕하십니까.\n"
            f"오늘 오전 10시에 {회기명} {회기유형}이(가) 개최됩니다.\n\n"
            f"위원님들께서는 원활한 진행을 위해\n"
            f"시간 맞춰 회의장으로 참석해 주시면 감사하겠습니다.\n\n"
            f"항상 의정활동에 노고가 많으십니다."
        )


def load_tasks_from_supabase():
    """Supabase에서 schedule 테이블 전체 조회"""
    tasks = []
    url = f"{SUPABASE_URL}/rest/v1/schedule?select=*&order=도시위원회의일.asc"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if not res.ok:
            print(f"❌ Supabase 조회 실패: {res.text}")
            return tasks

        rows = res.json()
        print(f"✅ {len(rows)}건 조회됨")

        for row in rows:
            if not row.get('회기명'):
                continue

            회기명 = row['회기명'].strip()
            회기유형 = row['회기유형'].strip()
            회기시작 = datetime.strptime(row['회기시작'].strip(), '%Y-%m-%d')
            상임위 = datetime.strptime(row['도시위원회의일'].strip(), '%Y-%m-%d')
            회기종료 = datetime.strptime(row['회기종료'].strip(), '%Y-%m-%d')
            의원발의 = row.get('의원발의여부', '').strip() if row.get('의원발의여부') else ''
            차수 = row.get('차수') or 0

            rule_key = next((k for k in TASK_RULES if k in 회기유형), None)
            if not rule_key:
                continue

            for rule in TASK_RULES[rule_key]:
                if rule.get('조건') == '의원발의' and 의원발의 != '있음':
                    continue
                base = {
                    '회기시작': 회기시작,
                    '상임위': 상임위,
                    '2차본회의': 회기종료
                }[rule['base']]
                task_date = base + timedelta(days=rule['offset'])
                비고 = '⏰ 아침' if rule.get('시각') == '아침' else '🔔 종료 후' if rule.get('시각') == '종료후' else ''

                tasks.append({
                    'date': task_date,
                    '회기명': 회기명,
                    '회기유형': 회기유형,
                    '할일': rule['label'],
                    '비고': 비고,
                    '상임위일': 상임위,
                    '차수': 차수
                })

    except Exception as e:
        print(f"❌ Supabase 로드 에러: {e}")

    return tasks


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 설정 없음, 출력만 합니다.")
        print(message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ 전송 에러: {e}")


def main():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today_date = now_kst.date()

    tasks = load_tasks_from_supabase()
    today_tasks = [t for t in tasks if t['date'].date() == today_date]

    if not today_tasks:
        print(f"오늘({today_date})은 할일이 없습니다.")
        return

    # 회기명별 그룹
    groups = {}
    for t in today_tasks:
        groups.setdefault(t['회기명'], []).append(t)

    today_str = now_kst.strftime('%Y년 %m월 %d일')
    msg = f'📋 <b>오늘의 도시위원회 실무 체크리스트</b>\n{today_str}\n{"─" * 20}\n\n'

    for 회기명, items in groups.items():
        msg += f'<b>【{회기명}】</b>\n'
        for t in items:
            차수_str = f"제{t['차수']}차 " if t['차수'] else ""
            msg += f'✅ [{차수_str}도시위원회] {t["할일"]} {t["비고"]}\n'
        msg += '\n'

    # 단톡방 안내문 미리보기
    for t in today_tasks:
        if '단톡방' in t['할일'] or '문자 발송' in t['할일']:
            msg_type = 'D-0' if '문자 발송' in t['할일'] else 'D-2'
            안내문 = get_dantalk_message(
                msg_type, t['상임위일'], t['회기명'], t['회기유형'], t['차수']
            )
            msg += f'{"─" * 20}\n💬 <b>단톡방 안내문 미리보기 (제{t["차수"]}차)</b>\n\n{안내문}\n'

    send_telegram(msg)


if __name__ == '__main__':
    main()
