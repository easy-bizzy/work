import streamlit as st
import pandas as pd
import json
from datetime import datetime
import requests

st.set_page_config(page_title="Учёт рабочего времени", page_icon="📊", layout="wide")

# ============================================
# НАСТРОЙКИ
# ============================================
API_KEY = "$2a$10$fdP3BAMcCh8G0kJpVurg7.fqWCvq9jsXK.yzOcd0ynCzs4H2PEoVC"
BIN_ID = "6a550654da38895dfe578dd3"

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
# ФУНКЦИИ ОБЛАКА
# ============================================
def load_from_cloud():
    headers = {'X-Master-Key': API_KEY}
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}/latest'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('record', {}), True
        return None, False
    except:
        return None, False

def save_to_cloud(data):
    headers = {'X-Master-Key': API_KEY, 'Content-Type': 'application/json'}
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    try:
        response = requests.put(url, headers=headers, json=data, timeout=10)
        return response.status_code == 200
    except:
        return False

# ============================================
# ИНИЦИАЛИЗАЦИЯ (Загрузка только один раз при старте сессии)
# ============================================
if 'hours_data' not in st.session_state:
    cloud_data, load_ok = load_from_cloud()
    if load_ok and cloud_data:
        st.session_state.hours_data = cloud_data.get('hours', {})
        st.session_state.feed = cloud_data.get('feed', [])
        st.session_state.votes = cloud_data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
        st.session_state.checkins = cloud_data.get('checkins', {})
        st.session_state.locked_data = cloud_data.get('locked', {})
    else:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.checkins = {}
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
        'checkins': st.session_state.checkins,
        'locked': st.session_state.locked_data
    }

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title("📊 Учёт часов")
st.sidebar.write(f"Записей в памяти: {len(st.session_state.hours_data)}")

if st.sidebar.button("💾 СОХРАНИТЬ В ОБЛАКО", type="primary", use_container_width=True):
    with st.spinner("Сохранение..."):
        ok = save_to_cloud(get_all_data())
        if ok:
            st.sidebar.success("✅ Сохранено!")
            st.success("Данные сохранены в облако!")
        else:
            st.sidebar.error("❌ Ошибка!")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "dashboard", "activity", "votes", "rating"])
month = st.sidebar.selectbox("📅 Месяц", MONTHS)

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
    st.title(f"️ Ввод часов - {month} 2026")
    
    cal = month_info
    days_count = DAYS_IN_MONTH[month]
    
    # CSS для цветных колонок
    css_rules = []
    for day in range(1, days_count + 1):
        col_index = day + 1
        if day in cal['holidays']:
            css_rules.append(f'div[data-testid="stDataFrame"] table tr th:nth-child({col_index}), div[data-testid="stDataFrame"] table tr td:nth-child({col_index}) {{ background-color: #FCA5A5 !important; color: #991B1B !important; }}')
        elif day in cal['short']:
            css_rules.append(f'div[data-testid="stDataFrame"] table tr th:nth-child({col_index}), div[data-testid="stDataFrame"] table tr td:nth-child({col_index}) {{ background-color: #FED7AA !important; color: #9A3412 !important; }}')
        elif day in cal['weekends']:
            css_rules.append(f'div[data-testid="stDataFrame"] table tr th:nth-child({col_index}), div[data-testid="stDataFrame"] table tr td:nth-child({col_index}) {{ background-color: #E9D5FF !important; color: #6B21A8 !important; }}')
    
    css_rules.append('div[data-testid="stDataFrame"] table tr th:nth-child(33), div[data-testid="stDataFrame"] table tr td:nth-child(33) { background-color: #86EFAC !important; color: #064E3B !important; font-weight: bold; }')
    css_rules.append('div[data-testid="stDataFrame"] table tr th:nth-child(34), div[data-testid="stDataFrame"] table tr td:nth-child(34) { background-color: #FDE047 !important; color: #713F12 !important; font-weight: bold; }')
    
    st.markdown(f'<style>{"".join(css_rules)}</style>', unsafe_allow_html=True)
    
    # Легенда
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 15px;">'
    for day in range(1, days_count + 1):
        if day in cal['holidays']:
            color, label = '#FCA5A5', f'🔴{day}'
        elif day in cal['short']:
            color, label = '#FED7AA', f'🟠{day}'
        elif day in cal['weekends']:
            color, label = '#E9D5FF', f'🟣{day}'
        else:
            color, label = '#374151', str(day)
        legend_html += f'<div style="background-color: {color}; color: white; padding: 4px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; min-width: 28px; text-align: center;">{label}</div>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)
    
    # Таблица
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
    
    if st.button("💾 СОХРАНИТЬ В ОБЛАКО И ЗАФИКСИРОВАТЬ", type="primary", use_container_width=True):
        saved_count = 0
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                if is_locked(month, emp):
                    st.warning(f"️ {emp} уже зафиксирован, пропускаем.")
                    continue
                
                new_hours = []
                total_emp = 0
                for day in range(1, days_count + 1):
                    val = edited_df.iloc[idx][str(day)]
                    try:
                        val = float(val)
                    except:
                        val = 0.0
                    new_hours.append(val)
                    total_emp += val
                
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                
                st.session_state.hours_data[f"{month}_{emp}"] = new_hours[:31]
                lock_data(month, emp)
                saved_count += 1
                
                if total_emp > 0:
                    add_to_feed(f'{emp}: {total_emp:.1f} ч', '⏱')
        
        st.write(f"**Сохранено записей: {saved_count}**")
        
        ok = save_to_cloud(get_all_data())
        if ok:
            st.success("✅ ДАННЫЕ СОХРАНЕНЫ В ОБЛАКО И ЗАФИКСИРОВАНЫ!")
            st.balloons()
        else:
            st.error("❌ ОШИБКА СОХРАНЕНИЯ!")
        st.rerun()
    
    st.markdown("---")
    st.markdown("**🔒 Статус блокировки:**")
    for emp in EMPLOYEES:
        if is_locked(month, emp):
            st.success(f"✅ {emp} - зафиксировано (нельзя менять)")
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
        locked_status = '🔒' if is_locked(month, emp) else '🔓'
        stats_list.append({
            'Сотрудник': f'{locked_status} {emp}',
            'Отработано часов': total,
            'Норма часов': norm,
            'Осталось часов': remaining_hours,
            'Процент выполнения': f'{efficiency:.1f}%',
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
    st.subheader("📈 Статистика")
    col1, col2, col3 = st.columns(3)
    with col1:
        top_worker = df.loc[df['Отработано часов'].idxmax()]
        st.metric("🏆 Лидер месяца", top_worker['Сотрудник'], f"{top_worker['Отработано часов']:.1f} ч")
    with col2:
        st.metric("🔥 Всего переработок", f"{df['Переработка'].sum():.1f} ч")
    with col3:
        completed = len(df[df['Осталось часов'] == 0])
        st.metric("✅ Выполнили норму", f'{completed} чел.')

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
            <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; color: white;">{item['emoji']} {item['message']}</span>
                    <span style="font-size: 12px; color: #94a3b8;">{item['time']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if st.button("🗑️ Очистить ленту"):
        st.session_state.feed = []
        save_to_cloud(get_all_data())
        st.rerun()

# ============================================
# ГОЛОСОВАНИЯ
# ============================================
elif page == "votes":
    st.title("️ Голосования недели")
    
    voter = st.selectbox("👤 Кто голосует?", ['— Выбери себя —'] + EMPLOYEES)
    
    if voter != '— Выбери себя —':
        already_voted = voter in st.session_state.votes['voters']
        if already_voted:
            st.success("✅ Ты уже проголосовал!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                hw_choice = st.radio("💪 Работящий:", [e for e in EMPLOYEES if e != voter], key='hw')
                if st.button("Голосовать за работящего"):
                    st.session_state.votes['hardworker'][voter] = hw_choice
                    st.session_state.votes['voters'].append(voter)
                    save_to_cloud(get_all_data())
                    st.success("✅ Голос засчитан!")
                    st.rerun()
            with col2:
                sl_choice = st.radio("😴 Халявщик:", [e for e in EMPLOYEES if e != voter], key='sl')
                if st.button("Голосовать за халявщика"):
                    st.session_state.votes['slacker'][voter] = sl_choice
                    if voter not in st.session_state.votes['voters']:
                        st.session_state.votes['voters'].append(voter)
                    save_to_cloud(get_all_data())
                    st.success("✅ Голос засчитан!")
                    st.rerun()
    
    st.markdown("---")
    st.subheader("📊 Результаты")
    hw_votes = {emp: sum(1 for v in st.session_state.votes['hardworker'].values() if v == emp) for emp in EMPLOYEES}
    sl_votes = {emp: sum(1 for v in st.session_state.votes['slacker'].values() if v == emp) for emp in EMPLOYEES}
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💪 Работящий:**")
        for emp, votes in sorted(hw_votes.items(), key=lambda x: x[1], reverse=True):
            if votes > 0: st.write(f"{emp}: {'█' * votes} ({votes})")
    with col2:
        st.markdown("**😴 Халявщик:**")
        for emp, votes in sorted(sl_votes.items(), key=lambda x: x[1], reverse=True):
            if votes > 0: st.write(f"{emp}: {'█' * votes} ({votes})")
    
    if st.button("🔄 Начать новое голосование"):
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        save_to_cloud(get_all_data())
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
        st.warning("⚠️ Нет данных за этот месяц.")
    else:
        st.markdown("---")
        st.subheader("🏆 Подиум")
        
        if len(df) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;">
                <h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3>
                <p><b>{df.iloc[1]["Часы"]:.1f} ч</b></p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:30px; border-radius:10px; text-align:center; border:3px solid gold;">
                <h1></h1><h2>{df.iloc[0]["Сотрудник"]}</h2>
                <p style="font-size:24px;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p>
                <p style="font-size:20px; color:#000;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background:#CD7F32; padding:20px; border-radius:10px; text-align:center;">
                <h2></h2><h3>{df.iloc[2]["Сотрудник"]}</h3>
                <p><b>{df.iloc[2]["Часы"]:.1f} ч</b></p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📋 Полный рейтинг")
        st.dataframe(df, use_container_width=True)
