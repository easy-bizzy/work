import streamlit as st
import pandas as pd
import requests
import base64
import json
from datetime import datetime

st.set_page_config(page_title="Учёт рабочего времени", page_icon="", layout="wide", initial_sidebar_state="expanded")

# ============================================
# НАСТРОЙКИ GITHUB
# ============================================
GITHUB_TOKEN = "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"
REPO_OWNER = "easy-bizzy"
REPO_NAME = "work"
FILE_PATH = "data.json"

def get_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def get_file_url():
    return f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

def load_from_github():
    try:
        r = requests.get(get_file_url(), headers=get_headers(), timeout=10)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            return json.loads(content), True
        return None, False
    except Exception as e:
        return None, False

def save_to_github(data):
    try:
        r = requests.get(get_file_url(), headers=get_headers(), timeout=10)
        sha = r.json()['sha'] if r.status_code == 200 else None
        encoded = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        payload = {"message": f"Update {datetime.now().strftime('%H:%M:%S')}", "content": encoded, "branch": "main"}
        if sha:
            payload["sha"] = sha
        r = requests.put(get_file_url(), headers=get_headers(), json=payload, timeout=10)
        return r.status_code in [200, 201]
    except Exception as e:
        return False

# ============================================
# ДАННЫЕ
# ============================================
EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']

MONTHS_DATA = {
    'ИЮЛЬ': {'norm': 184, 'workdays': 23, 'weekends': [4,5,11,12,18,19,25,26], 'holidays': [], 'short': []},
    'АВГУСТ': {'norm': 168, 'workdays': 21, 'weekends': [1,2,8,9,15,16,22,23,29,30], 'holidays': [], 'short': []},
    'СЕНТЯБРЬ': {'norm': 176, 'workdays': 22, 'weekends': [5,6,12,13,19,20,26,27], 'holidays': [], 'short': []},
    'ОКТЯБРЬ': {'norm': 176, 'workdays': 22, 'weekends': [3,4,10,11,17,18,24,25,31], 'holidays': [], 'short': []},
    'НОЯБРЬ': {'norm': 160, 'workdays': 20, 'weekends': [1,7,8,14,15,21,22,28,29], 'holidays': [4], 'short': [3]},
    'ДЕКАБРЬ': {'norm': 184, 'workdays': 23, 'weekends': [5,6,12,13,19,20,26,27], 'holidays': [], 'short': [31]},
}

DAYS_IN_MONTH = {'ИЮЛЬ': 31, 'АВГУСТ': 31, 'СЕНТЯБРЬ': 30, 'ОКТЯБРЬ': 31, 'НОЯБРЬ': 30, 'ДЕКАБРЬ': 31}

# ============================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================
if 'hours_data' not in st.session_state:
    data, ok = load_from_github()
    if ok and data:
        st.session_state.hours_data = data.get('hours', {})
        st.session_state.feed = data.get('feed', [])
        st.session_state.votes = data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
        st.session_state.locked_data = data.get('locked', {})
    else:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.locked_data = {}

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================
def get_hours(month, emp):
    key = f"{month}_{emp}"
    if key not in st.session_state.hours_data:
        st.session_state.hours_data[key] = [0.0] * 31
    return st.session_state.hours_data[key]

def is_locked(month, emp):
    return st.session_state.locked_data.get(f"{month}_{emp}", False)

def lock_data(month, emp):
    st.session_state.locked_data[f"{month}_{emp}"] = True

def add_to_feed(message, emoji=''):
    now = datetime.now().strftime('%d.%m %H:%M')
    st.session_state.feed.insert(0, {'time': now, 'emoji': emoji, 'message': message})
    if len(st.session_state.feed) > 50:
        st.session_state.feed = st.session_state.feed[:50]

def calc_stats(hours, norm, workdays):
    total = sum(hours)
    overtime = sum(max(0, h - 8) for h in hours if h > 0)
    efficiency = (total / norm * 100) if norm > 0 else 0
    remaining_hours = max(0, norm - total)
    workdays_worked = sum(1 for h in hours if h > 0)
    remaining_days = max(0, workdays - workdays_worked)
    return total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days

def get_all_data():
    return {
        'hours': st.session_state.hours_data,
        'feed': st.session_state.feed,
        'votes': st.session_state.votes,
        'locked': st.session_state.locked_data
    }

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title(" Учёт часов")
st.sidebar.write(f"Записей: {len(st.session_state.hours_data)}")

if st.sidebar.button("💾 СОХРАНИТЬ В GITHUB", type="primary", use_container_width=True):
    with st.spinner("Сохранение..."):
        ok = save_to_github(get_all_data())
        if ok:
            st.sidebar.success("✅ Сохранено!")
            st.success("Данные сохранены в GitHub!")
        else:
            st.sidebar.error("❌ Ошибка сохранения!")

if st.sidebar.button("🔄 Загрузить из GitHub", use_container_width=True):
    with st.spinner("Загрузка..."):
        data, ok = load_from_github()
        if ok and data:
            st.session_state.hours_data = data.get('hours', {})
            st.session_state.feed = data.get('feed', [])
            st.session_state.votes = data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
            st.session_state.locked_data = data.get('locked', {})
            st.sidebar.success("✅ Загружено!")
            st.rerun()
        else:
            st.sidebar.error("❌ Ошибка загрузки!")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "dashboard", "activity", "votes", "rating"])
month = st.sidebar.selectbox(" Месяц", MONTHS)

month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{month} 2026**")
st.sidebar.markdown(f"Рабочих дней: **{workdays}**")
st.sidebar.markdown(f"Норма часов: **{norm}**")

# ============================================
# ВВОД ЧАСОВ
# ============================================
if page == "input":
    st.title(f"⏱️ Ввод часов - {month} 2026")

    cal = month_info
    days_count = DAYS_IN_MONTH[month]

    css_rules = []
    for day in range(1, days_count + 1):
        ci = day + 1
        if day in cal['holidays']:
            css_rules.append(f'div[data-testid="stDataFrame"] table tr th:nth-child({ci}), div[data-testid="stDataFrame"] table tr td:nth-child({ci}) {{ background-color: #FCA5A5 !important; color: #991B1B !important; }}')
        elif day in cal['short']:
            css_rules.append(f'div[data-testid="stDataFrame"] table tr th:nth-child({ci}), div[data-testid="stDataFrame"] table tr td:nth-child({ci}) {{ background-color: #FED7AA !important; color: #9A3412 !important; }}')
        elif day in cal['weekends']:
            css_rules.append(f'div[data-testid="stDataFrame"] table tr th:nth-child({ci}), div[data-testid="stDataFrame"] table tr td:nth-child({ci}) {{ background-color: #E9D5FF !important; color: #6B21A8 !important; }}')
    css_rules.append('div[data-testid="stDataFrame"] table tr th:nth-child(33), div[data-testid="stDataFrame"] table tr td:nth-child(33) { background-color: #86EFAC !important; font-weight: bold; }')
    css_rules.append('div[data-testid="stDataFrame"] table tr th:nth-child(34), div[data-testid="stDataFrame"] table tr td:nth-child(34) { background-color: #FDE047 !important; font-weight: bold; }')
    st.markdown(f'<style>{"".join(css_rules)}</style>', unsafe_allow_html=True)

    legend = '<div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:15px;">'
    for day in range(1, days_count + 1):
        if day in cal['holidays']: c, l = '#FCA5A5', f'🔴{day}'
        elif day in cal['short']: c, l = '#FED7AA', f'🟠{day}'
        elif day in cal['weekends']: c, l = '#E9D5FF', f'🟣{day}'
        else: c, l = '#374151', str(day)
        legend += f'<div style="background:{c};color:white;padding:4px 6px;border-radius:4px;font-size:11px;font-weight:bold;min-width:28px;text-align:center;">{l}</div>'
    legend += '</div>'
    st.markdown(legend, unsafe_allow_html=True)

    table_data = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        row = {'Сотрудник': emp}
        for day in range(1, days_count + 1):
            row[str(day)] = float(hours[day-1]) if day-1 < len(hours) else 0.0
        total = sum(row[str(d)] for d in range(1, days_count + 1))
        overtime = sum(max(0, row[str(d)] - 8) for d in range(1, days_count + 1) if row[str(d)] > 0)
        row['ИТОГО'] = round(total, 1)
        row['ПЕРЕРАБ'] = round(overtime, 1)
        table_data.append(row)

    df_input = pd.DataFrame(table_data)
    column_config = {
        'Сотрудник': st.column_config.TextColumn('Сотрудник', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', disabled=True),
        'ПЕРЕРАБ': st.column_config.NumberColumn('ПЕРЕРАБ', format='%.1f', disabled=True),
    }
    for day in range(1, days_count + 1):
        column_config[str(day)] = st.column_config.NumberColumn(str(day), min_value=0.0, max_value=24.0, step=0.5, format='%.1f', width='small')

    edited_df = st.data_editor(df_input, column_config=column_config, hide_index=True, use_container_width=True, num_rows='fixed', key='hours_table')

    st.markdown("---")

    if st.button("💾 СОХРАНИТЬ ДАННЫЕ", type="primary", use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                if is_locked(month, emp):
                    continue
                new_hours = []
                total_emp = 0
                for day in range(1, days_count + 1):
                    try: val = float(edited_df.iloc[idx][str(day)])
                    except: val = 0.0
                    new_hours.append(val)
                    total_emp += val
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                st.session_state.hours_data[f"{month}_{emp}"] = new_hours[:31]
                lock_data(month, emp)
                if total_emp > 0:
                    add_to_feed(f'{emp}: {total_emp:.1f} ч', '')

        ok = save_to_github(get_all_data())
        if ok:
            st.success("✅ ДАННЫЕ СОХРАНЕНЫ В GITHUB!")
            st.balloons()
        else:
            st.error("❌ ОШИБКА СОХРАНЕНИЯ!")
        st.rerun()

    st.markdown("---")
    st.markdown("**🔒 Статус блокировки:**")
    for emp in EMPLOYEES:
        if is_locked(month, emp):
            st.success(f"✅ {emp} - зафиксировано")
        else:
            st.warning(f"⚠️ {emp} - можно редактировать")

# ============================================
# ДАШБОРД
# ============================================
elif page == "dashboard":
    st.title(f"📊 Дашборд - {month} 2026")

    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days = calc_stats(hours, norm, workdays)
        locked = '🔒' if is_locked(month, emp) else '🔓'
        stats_list.append({
            'Сотрудник': f'{locked} {emp}',
            'Отработано часов': total,
            'Норма часов': norm,
            'Осталось часов': remaining_hours,
            '% выполнения': f'{efficiency:.1f}%',
            'Отработано дней': workdays_worked,
            'Переработка': overtime
        })

    df = pd.DataFrame(stats_list)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⏱ Часы vs Норма")
        if not df.empty:
            st.bar_chart(df.set_index('Сотрудник')[['Отработано часов', 'Норма часов']])
    with col2:
        st.subheader("🔥 Переработка")
        if not df.empty:
            st.bar_chart(df.set_index('Сотрудник')['Переработка'])

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        top = df.loc[df['Отработано часов'].idxmax()]
        st.metric("🏆 Лидер", top['Сотрудник'], f"{top['Отработано часов']:.1f} ч")
    with col2:
        st.metric("🔥 Переработок", f"{df['Переработка'].sum():.1f} ч")
    with col3:
        done = len(df[df['Осталось часов'] == 0])
        st.metric("✅ Выполнили норму", f'{done} чел.')

# ============================================
# ЛЕНТА АКТИВНОСТИ
# ============================================
elif page == "activity":
    st.title("📱 Лента активности")

    if len(st.session_state.feed) == 0:
        st.info("📭 Лента пуста.")
    else:
        for item in st.session_state.feed:
            st.markdown(f"""
            <div style="background:#1e293b;padding:15px;border-radius:10px;margin-bottom:10px;border-left:4px solid #3b82f6;">
                <span style="font-size:14px;color:white;">{item['emoji']} {item['message']}</span>
                <span style="font-size:12px;color:#94a3b8;float:right;">{item['time']}</span>
            </div>
            """, unsafe_allow_html=True)

    if st.button("🗑️ Очистить ленту"):
        st.session_state.feed = []
        save_to_github(get_all_data())
        st.rerun()

# ============================================
# ГОЛОСОВАНИЯ
# ============================================
elif page == "votes":
    st.title("🗳️ Голосования недели")

    voter = st.selectbox("👤 Кто голосует?", ['— Выбери себя —'] + EMPLOYEES)

    if voter != '— Выбери себя —':
        already = voter in st.session_state.votes['voters']
        if already:
            st.success("✅ Ты уже проголосовал!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                hw = st.radio("💪 Работящий:", [e for e in EMPLOYEES if e != voter], key='hw')
                if st.button("Голосовать за работящего"):
                    st.session_state.votes['hardworker'][voter] = hw
                    st.session_state.votes['voters'].append(voter)
                    save_to_github(get_all_data())
                    st.success("✅ Голос засчитан!")
                    st.rerun()
            with col2:
                sl = st.radio("😴 Халявщик:", [e for e in EMPLOYEES if e != voter], key='sl')
                if st.button("Голосовать за халявщика"):
                    st.session_state.votes['slacker'][voter] = sl
                    if voter not in st.session_state.votes['voters']:
                        st.session_state.votes['voters'].append(voter)
                    save_to_github(get_all_data())
                    st.success("✅ Голос засчитан!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📊 Результаты")
    hw_votes = {e: sum(1 for v in st.session_state.votes['hardworker'].values() if v == e) for e in EMPLOYEES}
    sl_votes = {e: sum(1 for v in st.session_state.votes['slacker'].values() if v == e) for e in EMPLOYEES}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💪 Работящий:**")
        for e, v in sorted(hw_votes.items(), key=lambda x: x[1], reverse=True):
            if v > 0: st.write(f"{e}: {'█' * v} ({v})")
    with col2:
        st.markdown("**😴 Халявщик:**")
        for e, v in sorted(sl_votes.items(), key=lambda x: x[1], reverse=True):
            if v > 0: st.write(f"{e}: {'█' * v} ({v})")

    if st.button("🔄 Новое голосование"):
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        save_to_github(get_all_data())
        st.rerun()

# ============================================
# РЕЙТИНГ
# ============================================
elif page == "rating":
    st.title(f"🏆 Рейтинг - {month}")

    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, *_ = calc_stats(hours, norm, workdays)
        stats_list.append({'Сотрудник': emp, 'Часы': total, 'Переработка': overtime, 'Эффективность %': round(efficiency, 1)})

    df = pd.DataFrame(stats_list).sort_values('Часы', ascending=False).reset_index(drop=True)

    if df['Часы'].sum() == 0:
        st.warning("️ Нет данных.")
    else:
        if len(df) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div style="background:#C0C0C0;padding:20px;border-radius:10px;text-align:center;"><h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3><p><b>{df.iloc[1]["Часы"]:.1f} ч</b></p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="background:linear-gradient(135deg,#FFD700,#FFA500);padding:30px;border-radius:10px;text-align:center;border:3px solid gold;"><h1>🥇</h1><h2>{df.iloc[0]["Сотрудник"]}</h2><p style="font-size:24px;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p><p style="color:#000;font-size:20px;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div style="background:#CD7F32;padding:20px;border-radius:10px;text-align:center;"><h2>🥉</h2><h3>{df.iloc[2]["Сотрудник"]}</h3><p><b>{df.iloc[2]["Часы"]:.1f} ч</b></p></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.dataframe(df, use_container_width=True)
