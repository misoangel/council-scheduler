import csv
import os
import requests
from datetime import datetime, timedelta

# ================================================================
# 도시위원회 업무 알림 시스템
# ================================================================

TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ----------------------------------------------------------------
# D-day 역산 규칙
# ----------------------------------------------------------------
TASK_RULES = {

    '안건심사': [
        {'label': '발의문 제출 마감 확인',                                           'base': '회기시작',  'offset': -10},
        {'label': '입법예고 시작',                                                   'base': '회기시작',  'offset': -10},
        {'label': '검토보고서 초안 작성 → 전문위원 전달',                             'base': '상임위',    'offset': -5 },
        {'label': '회의 진행 시나리오 작성 완료',                                     'base': '상임위',    'offset': -3 },
        {'label': '오늘의 의사일정 작성 완료',                                        'base': '상임위',    'offset': -3 },
        {'label': '사무보고서 작성 완료',                                             'base': '상임위',    'offset': -3 },
        {'label': '제안설명 시나리오 작성 완료 (의원발의)',                            'base': '상임위',    'offset': -3, '조건': '의원발의'},
        {'label': '전문위원 검토보고서 최종 확정',                                    'base': '상임위',    'offset': -2 },
        {'label': '단톡방 — 검토보고서 + 의사일정 + 회의 안내 송부',                  'base': '상임위',    'offset': -2 },
        {'label': '출력 — 검토보고서 10부, 시나리오 4부, 의사일정 13부, 사무보고 1부, 제안설명시나리오 1부', 'base': '상임위', 'offset': -2},
        {'label': '출력 — 의원발의 발의문 10부',                                      'base': '상임위',    'offset': -2, '조건': '의원발의'},
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)',                             'base': '상임위',    'offset': 0,  '시각': '아침'},
        {'label': '결과보고 공문 → 운영위 담당자 송부',                               'base': '상임위',    'offset': 0,  '시각': '종료후'},
        {'label': '심사보고서 + 심사보고 시나리오 작성 완료',                         'base': '2차본회의', 'offset': -2 },
        {'label': '심사보고서 21부 출력',                                             'base': '2차본회의', 'offset': -1 },
        {'label': '시나리오 출력 → 도시위원장 공유 + 비치 준비',                      'base': '2차본회의', 'offset': -1 },
    ],

    '추경심사': [
        {'label': '추경 예산서 회부 확인',                                           'base': '회기시작',  'offset': -10},
        {'label': '검토보고서 초안 작성 → 전문위원 전달 (이호조·예산서 참고)',         'base': '상임위',    'offset': -5 },
        {'label': '기금운용계획안 포함 여부 확인',                                    'base': '상임위',    'offset': -5 },
        {'label': '회의 진행 시나리오 작성 완료',                                     'base': '상임위',    'offset': -3 },
        {'label': '오늘의 의사일정 작성 완료',                                        'base': '상임위',    'offset': -3 },
        {'label': '사무보고서 작성 완료',                                             'base': '상임위',    'offset': -3 },
        {'label': '페이지목록 작성 완료',                                             'base': '상임위',    'offset': -3 },
        {'label': '전문위원 검토보고서 최종 확정',                                    'base': '상임위',    'offset': -2 },
        {'label': '단톡방 — 검토보고서 + 의사일정 + 회의 안내 송부',                  'base': '상임위',    'offset': -2 },
        {'label': '출력 — 검토보고서 10부, 시나리오 4부, 의사일정 13부, 사무보고 1부, 페이지목록 13부', 'base': '상임위', 'offset': -2},
        {'label': '계수조정 시나리오 + 계수조정 목록 준비 완료',                      'base': '상임위',    'offset': -2 },
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)',                             'base': '상임위',    'offset': 0,  '시각': '아침'},
        {'label': '결과보고 공문 → 운영위 담당자 송부',                               'base': '상임위',    'offset': 0,  '시각': '종료후'},
        {'label': '예비심사보고서 + 시나리오 즉시 작성 → 예결위 담당자 송부',         'base': '상임위',    'offset': 0,  '시각': '종료후'},
        {'label': '출력 — 예비심사보고서 11부, 시나리오 1부 → 예결위 전달',           'base': '상임위',    'offset': 0,  '시각': '종료후'},
    ],

    '업무보고': [
        {'label': '회의 진행 시나리오 작성 완료',                                     'base': '상임위',    'offset': -3 },
        {'label': '오늘의 의사일정 작성 완료',                                        'base': '상임위',    'offset': -3 },
        {'label': '사무보고서 작성 완료',                                             'base': '상임위',    'offset': -3 },
        {'label': '단톡방 — 의사일정 + 회의 안내 송부',                               'base': '상임위',    'offset': -2 },
        {'label': '출력 — 시나리오 4부, 의사일정 13부, 사무보고 1부',                 'base': '상임위',    'offset': -2 },
        {'label': '집행부 제출 자료 세팅 확인',                                       'base': '상임위',    'offset': -2 },
        {'label': '📱 회의 진행 안내 문자 발송 (단톡방)',                             'base': '상임위',    'offset': 0,  '시각': '아침'},
        {'label': '결과보고 공문 → 운영위 담당자 송부',                               'base': '상임위',    'offset': 0,  '시각': '종료후'},
    ]
}


# ----------------------------------------------------------------
# 단톡방 안내문 양식
# ----------------------------------------------------------------
def get_dantalk_message(msg_type, 상임위일, 회기명):
    days = ['일', '월', '화', '수', '목', '금', '토']
    date_str = 상임위일.strftime('%Y. %-m. %-d.')
    day_str = days[상임위일.weekday() + 1 if 상임위일.weekday() < 6 else 0]
    # Python weekday: 월=0 ~ 일=6, 한국식: 일=0 ~ 토=6
    day_map = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}
    day_str = day_map[상임위일.weekday()]

    if msg_type == 'D-2':
        return f"""안녕하십니까, 도시위원회 전문위원입니다.

오는 {date_str}({day_str}) {회기명} 도시위원회가 개최될 예정입니다.

📅 일시 : {date_str}({day_str}) 10:00
📍 장소 : 도시위원회 회의실

검토보고서 및 오늘의 의사일정을 함께 송부드리오니 참고하시기 바랍니다.

감사합니다."""

    if msg_type == 'D-0':
        return f"""안녕하십니까, 도시위원회 전문위원입니다.

오늘 {date_str}({day_str}) 도시위원회가 개최됩니다.

📅 일시 : {date_str}({day_str}) 10:00
📍 장소 : 도시위원회 회의실

위원님들의 참석을 부탁드립니다.

감사합니다."""


# ----------------------------------------------------------------
# 일정 로드 및 D-day 역산
# ----------------------------------------------------------------
def load_tasks():
    tasks = []
    with open('schedule.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            회기명      = row['회기명'].strip()
            회기유형    = row['회기유형'].strip()
            회기시작    = datetime.strptime(row['회기시작'].strip(), '%Y-%m-%d')
            회기종료    = datetime.strptime(row['회기종료'].strip(), '%Y-%m-%d')
            상임위      = datetime.strptime(row['상임위회의일'].strip(), '%Y-%m-%d')
            의원발의    = row['의원발의여부'].strip()
            이차본회의  = 회기종료

            rules = TASK_RULES.get(회기유형, [])
            for rule in rules:
                # 조건 체크
                if rule.get('조건') == '의원발의' and 의원발의 != '있음':
                    continue

                # 기준일 결정
                if rule['base'] == '회기시작':
                    base = 회기시작
                elif rule['base'] == '상임위':
                    base = 상임위
                elif rule['base'] == '2차본회의':
                    base = 이차본회의

                task_date = base + timedelta(days=rule['offset'])
                비고 = ''
                if rule.get('시각') == '아침':
                    비고 = '⏰ 아침'
                elif rule.get('시각') == '종료후':
                    비고 = '🔔 회의 종료 후'

                tasks.append({
                    'date':     task_date,
                    '회기명':   회기명,
                    '회기유형': 회기유형,
                    '할일':     rule['label'],
                    '비고':     비고,
                    '상임위일': 상임위,
                })
    return tasks


# ----------------------------------------------------------------
# 오늘 할일 필터링
# ----------------------------------------------------------------
def get_today_tasks(tasks):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return [t for t in tasks if t['date'].date() == today.date()]


# ----------------------------------------------------------------
# 텔레그램 발송
# ----------------------------------------------------------------
def send_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, json={
        'chat_id':    TELEGRAM_CHAT_ID,
        'text':       message,
        'parse_mode': 'HTML'
    })


# ----------------------------------------------------------------
# 메인 실행
# ----------------------------------------------------------------
def main():
    tasks     = load_tasks()
    today_tasks = get_today_tasks(tasks)

    if not today_tasks:
        print('오늘 할일 없음')
        return

    # 회기별 그룹핑
    groups = {}
    for t in today_tasks:
        if t['회기명'] not in groups:
            groups[t['회기명']] = []
        groups[t['회기명']].append(t)

    today_str = datetime.now().strftime('%Y년 %-m월 %-d일')
    msg = f'📋 <b>도시위원회 오늘의 업무 알림</b>\n{today_str}\n{"─" * 20}\n\n'

    for 회기명, items in groups.items():
        msg += f'<b>【{회기명}】</b>\n'
        for t in items:
            msg += f'✅ {t["할일"]}'
            if t['비고']:
                msg += f' {t["비고"]}'
            msg += '\n'
        msg += '\n'

    # 단톡방 안내문 필요한 항목
    dantalk_items = [t for t in today_tasks if '단톡방' in t['할일'] or '문자 발송' in t['할일']]
    for t in dantalk_items:
        msg_type = 'D-0' if '문자 발송' in t['할일'] else 'D-2'
        안내문 = get_dantalk_message(msg_type, t['상임위일'], t['회기명'])
        msg += f'{"─" * 20}\n'
        msg += f'💬 <b>단톡방 안내문</b> ({t["회기명"]} · {"당일" if msg_type == "D-0" else "D-2"})\n\n'
        msg += 안내문 + '\n'

    send_telegram(msg)
    print('텔레그램 발송 완료')


if __name__ == '__main__':
    main()
