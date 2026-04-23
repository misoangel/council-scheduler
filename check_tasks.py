import csv
import os
import requests
import sys
from datetime import datetime, timedelta

# 1. 환경 변수 로드 (ID를 문자열로 먼저 받고, 공백 제거)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
raw_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
# ID가 마이너스(-)로 시작하거나 숫자인 경우를 모두 대비해 문자열 그대로 사용
TELEGRAM_CHAT_ID = raw_id

# [기존 TASK_RULES 및 get_dantalk_message 함수 부분은 주무관님 파일과 동일하므로 생략 가능하나, 
# 안전을 위해 제가 앞서 드린 전체 구조를 유지해 주세요.]

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

def get_dantalk_message(msg_type, 상임위일, 회기명, 회기유형):
    date_str = 상임위일.strftime('%y.%-m.%-d.')
    day_map = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}
    day_str = day_map[상임위일.weekday()]
    if msg_type == 'D-2':
        msg = f"📢 {회기명}\n     제1차 도시위원회 일정 알림\n━━━━━━━━━━━━━━\n• 일시: {date_str}({day_str}) 10:00\n• 안건: {회기유형}\n\n ⭐ 준비사항:\n  - 검토보고서\n  - 오늘의 의사일정"
        if any(x in 회기유형 for x in ['예산', '추경']):
            msg += "\n  - 사업명세서\n  - 사업설명서"
        msg += "\n\n붙임: 오늘의 의사일정, 검토보고서"
        return msg
    if msg_type == 'D-0':
        return f"🔔 오늘({date_str}) 도시위원회 회의 안내\n\n위원님, 안녕하십니까.\n오늘 오전 10시에 도시위원회 회의가 개최됩니다.\n\n위원님들께서는 원활한 회의 진행을 위해\n시간 맞춰 회의장으로 참석해 주시면 감사하겠습니다.\n\n항상 의정활동에 노고가 많으십니다."

def load_tasks():
    tasks = []
    if not os.path.exists('schedule.csv'): return []
    with open('schedule.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            회기명 = row['회기명'].strip()
            회기유형 = row['회기유형'].strip()
            회기시작 = datetime.strptime(row['회기시작'].strip(), '%Y-%m-%d')
            상임위 = datetime.strptime(row['상임위회의일'].strip(), '%Y-%m-%d')
            회기종료 = datetime.strptime(row['회기종료'].strip(), '%Y-%m-%d')
            의원발의 = row.get('의원발의여부', '').strip()
            for rule in TASK_RULES.get(회기유형, []):
                if rule.get('조건') == '의원발의' and 의원발의 != '있음': continue
                base = {'회기시작': 회기시작, '상임위': 상임위, '2차본회의': 회기종료}[rule['base']]
                task_date = base + timedelta(days=rule['offset'])
                비고 = '⏰ 아침' if rule.get('시각') == '아침' else '🔔 종료 후' if rule.get('시각') == '종료후' else ''
                tasks.append({
                    'date': task_date, '회기명': 회기명, '회기유형': 회기유형,
                    '할일': rule['label'], '비고': 비고, '상임위일': 상임위
                })
    return tasks

# ✅ 4. 텔레그램 발송 (가장 원시적이고 확실한 방식으로 복구)
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 토큰 또는 ID 누락")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # 예전 방식처럼 data 파라미터를 사용하여 안정성 확보
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ 텔레그램 전송 성공")
        else:
            print(f"❌ 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

def main():
    now_kst = datetime.now() + timedelta(hours=9)
    today_date = now_kst.date()

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        send_test_preview(now_kst)
        return

    tasks = load_tasks()
    today_tasks = [t for t in tasks if t['date'].date() == today_date]

    if not today_tasks:
        today_str = now_kst.strftime('%Y년 %-m월 %-d일')
        send_telegram(f"✅ <b>{today_str} 알림</b>\n\n오늘은 예정된 일정이 없습니다.")
        return

    groups = {}
    for t in today_tasks:
        groups.setdefault(t['회기명'], []).append(t)

    today_str = now_kst.strftime('%Y년 %-m월 %-d일')
    msg = f'📋 <b>오늘의 도시위원회 실무 체크리스트</b>\n{today_str}\n{"─" * 20}\n\n'
    for 회기명, items in groups.items():
        msg += f'<b>【{회기명}】</b>\n'
        for t in items:
            msg += f'✅ {t["할일"]} {t["비고"]}\n'
        msg += '\n'

    for t in today_tasks:
        if '단톡방' in t['할일'] or '문자 발송' in t['할일']:
            msg_type = 'D-0' if '문자 발송' in t['할일'] else 'D-2'
            안내문 = get_dantalk_message(msg_type, t['상임위일'], t['회기명'], t['회기유형'])
            msg += f'{"─" * 20}\n💬 <b>단톡방 안내문 미리보기</b>\n\n{안내문}\n'

    send_telegram(msg)

def send_test_preview(now_kst):
    test_date = now_kst
    test_회기 = "제999회 테스트회기"
    
    msg = "🧪 <b>봇 작동 테스트 모드</b>\n연결 성공! 모든 양식을 출력합니다.\n\n"
    
    # 1. D-2 안건심사 양식
    msg += "<b>[1. 안건심사 D-2 양식]</b>\n"
    msg += get_dantalk_message('D-2', test_date, test_회기, '안건심사') + "\n\n"
    
    # 2. D-2 본예산심사 양식 (사업명세서 포함 여부 확인용)
    msg += "<b>[2. 본예산심사 D-2 양식]</b>\n"
    msg += get_dantalk_message('D-2', test_date, test_회기, '본예산심사') + "\n\n"
    
    # 3. D-0 당일 양식
    msg += "<b>[3. 당일 아침 양식]</b>\n"
    msg += get_dantalk_message('D-0', test_date, test_회기, '안건심사')
    
    send_telegram(msg)

if __name__ == '__main__':
    main()
