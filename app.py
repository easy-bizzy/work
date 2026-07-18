import streamlit as st
import pandas as pd
import requests
import base64
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Учёт рабочего времени", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ============================================
# НАСТРОЙКИ GITHUB
# ============================================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_OWNER = "easy-bizzy"
REPO_NAME = "work"
FILE_PATH = "data.json"

if not GITHUB_TOKEN:
    st.error("❌ Токен не найден! Добавь GITHUB_TOKEN в Streamlit Secrets.")
    st.stop()

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
    except:
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
    except:
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
MONTH_NUM = {'ИЮЛЬ': 7, 'АВГУСТ': 8, 'СЕНТЯБРЬ': 9, 'ОКТЯБРЬ': 10, 'НОЯБРЬ': 11, 'ДЕКАБРЬ': 12}

# Дни недели для 2026 года
WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

def get_weekday(month, day):
    """Получить день недели для даты"""
    month_num = MONTH_NUM[month]
    dt = datetime(2026, month_num, day)
    return WEEKDAYS[dt.weekday()]

def is_weekend_day(month, day):
    """Проверка: выходной ли день недели (Сб или Вс)"""
    wd = get_weekday(month, day)
    return wd in ['Сб', 'Вс']

# ============================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================
if 'hours_data' not in st.session_state:
    data, ok = load_from_github()
    if ok and data:
        st.session_state.hours_data = data.get('hours', {})
        st.session_state.feed = data.get('feed', [])
        st.session_state.votes = data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
        st.session_state.leaves = data.get('leaves', [])
    else:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.leaves = []

# ============================================
# ФУНКЦИИ
# ============================================
def get_hours(month, emp):
    key = f"{month}_{emp}"
    if key not in st.session_state.hours_data:
        st.session_state.hours_data[key] = [0.0] * 31
    return st.session_state.hours_data[key]

def is_weekend(month, day):
    cal = MONTHS_DATA[month]
    return day in cal['weekends'] or day in cal['holidays']

def is_short(month, day):
    cal = MONTHS_DATA[month]
    return day in cal['short']

def get_leave_hours(month, emp):
    """Возвращает словарь {день: (часы, тип)} для отпуска/учебы/больничного"""
    leave_hours = {}
    month_num = MONTH_NUM[month]
    days_in = DAYS_IN_MONTH[month]
    
    for leave in st.session_state.leaves:
        if leave['emp'] != emp:
            continue
        start = datetime.strptime(leave['start'], '%Y-%m-%d')
        end = datetime.strptime(leave['end'], '%Y-%m-%d')
        
        month_start = datetime(2026, month_num, 1)
        month_end = datetime(2026, month_num, days_in)
        
        if start > month_end or end < month_start:
            continue
        
        actual_start = max(start, month_start)
        actual_end = min(end, month_end)
        
        current = actual_start
        while current <= actual_end:
            day = current.day
            if 1 <= day <= days_in:
                if leave['type'] == 'больничный':
                    leave_hours[day] = (0.0, 'больничный')
                elif is_weekend(month, day):
                    leave_hours[day] = (0.0, leave['type'])
                else:
                    leave_hours[day] = (8.0, leave['type'])
            current += timedelta(days=1)
    
    return leave_hours

def add_to_feed(message, emoji=''):
    now = datetime.now().strftime('%d.%m %H:%M')
    st.session_state.feed.insert(0, {'time': now, 'emoji': emoji, 'message': message})
    if len(st.session_state.feed) > 50:
        st.session_state.feed = st.session_state.feed[:50]

def calc_stats(hours, norm, workdays, month, emp):
    leave_hours = get_leave_hours(month, emp)
    leave_days_count = len([d for d, (h, t) in leave_hours.items() if h > 0])
    
    total = 0.0
    overtime = 0.0
    workdays_worked = 0
    
    for day_idx in range(31):
        day = day_idx + 1
        h = hours[day_idx] if day_idx < len(hours) else 0.0
        
        if day in leave_hours:
            leave_h, leave_type = leave_hours[day]
            total += leave_h
            if leave_h > 0:
                workdays_worked += 1
            continue
        
        if h > 0:
            total += h
            workdays_worked += 1
            
            if is_weekend(month, day):
                overtime += h
            elif h > 8:
                overtime += (h - 8)
    
    efficiency = (total / norm * 100) if norm > 0 else 0
    remaining_hours = max(0, norm - total)
    remaining_days = max(0, workdays - workdays_worked)
    
    return total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days, leave_days_count

def get_all_data():
    return {
        'hours': st.session_state.hours_data,
        'feed': st.session_state.feed,
        'votes': st.session_state.votes,
        'leaves': st.session_state.leaves
    }

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title("📊 Учёт часов")
st.sidebar.write(f"Записей: {len(st.session_state.hours_data)}")
st.sidebar.write(f"Отпусков/учеб: {len(st.session_state.leaves)}")

if st.sidebar.button("💾 СОХРАНИТЬ В GITHUB", type="primary", use_container_width=True):
    with st.spinner("Сохранение..."):
        ok = save_to_github(get_all_data())
        if ok:
            st.sidebar.success("✅ Сохранено!")
            st.success("Данные сохранены в GitHub!")
        else:
            st.sidebar.error("❌ Ошибка!")

if st.sidebar.button("🔄 Загрузить из GitHub", use_container_width=True):
    with st.spinner("Загрузка..."):
        data, ok = load_from_github()
        if ok and data:
            st.session_state.hours_data = data.get('hours', {})
            st.session_state.feed = data.get('feed', [])
            st.session_state.votes = data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
            st.session_state.leaves = data.get('leaves', [])
            st.sidebar.success("✅ Загружено!")
            st.rerun()
        else:
            st.sidebar.error("❌ Ошибка загрузки!")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "leaves", "dashboard", "activity", "votes", "rating"])
month = st.sidebar.selectbox("📅 Месяц", MONTHS)

month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{month} 2026**")
st.sidebar.markdown(f"Рабочих дней: **{workdays}**")
st.sidebar.markdown(f"Норма часов: **{norm}**")

# ============================================
# ВВОД ЧАСОВ С ДНЯМИ НЕДЕЛИ И ОТПУСКАМИ
# ============================================
if page == "input":
    st.title(f"⏱️ Ввод часов - {month} 2026")

    cal = month_info
    days_count = DAYS_IN_MONTH[month]

    # CSS для цветных колонок
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
    css_rules.append('div[data-testid="stDataFrame"] table tr th:nth-child(35), div[data-testid="stDataFrame"] table tr td:nth-child(35) { background-color: #A7F3D0 !important; color: #065F46 !important; font-weight: bold; }')
    css_rules.append('div[data-testid="stDataFrame"] table tr th:nth-child(36), div[data-testid="stDataFrame"] table tr td:nth-child(36) { background-color: #BFDBFE !important; color: #1E40AF !important; font-weight: bold; }')
    st.markdown(f'<style>{"".join(css_rules)}</style>', unsafe_allow_html=True)

    # Легенда дней недели
    weekday_legend = '<div style="display:flex;flex-wrap:wrap;gap:2px;margin-bottom:10px;">'
    for day in range(1, days_count + 1):
        wd = get_weekday(month, day)
        if wd in ['Сб', 'Вс']:
            color = '#E9D5FF'
            text_color = '#6B21A8'
        else:
            color = '#374151'
            text_color = 'white'
        weekday_legend += f'<div style="background:{color};color:{text_color};padding:3px 5px;border-radius:3px;font-size:10px;font-weight:bold;min-width:28px;text-align:center;">{day}<br>{wd}</div>'
    weekday_legend += '</div>'
    st.markdown("**📅 Дни месяца и дни недели:**")
    st.markdown(weekday_legend, unsafe_allow_html=True)

    # Таблица с днями недели, отпуском и учебой
    table_data = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        leave_hours = get_leave_hours(month, emp)
        row = {'Сотрудник': emp}
        
        leave_total = 0.0
        study_total = 0.0
        
        for day in range(1, days_count + 1):
            if day in leave_hours:
                leave_h, leave_type = leave_hours[day]
                row[str(day)] = leave_h
                if leave_type == 'отпуск' and leave_h > 0:
                    leave_total += leave_h
                elif leave_type == 'учеба' and leave_h > 0:
                    study_total += leave_h
            else:
                row[str(day)] = float(hours[day-1]) if day-1 < len(hours) else 0.0
        
        total = sum(row[str(d)] for d in range(1, days_count + 1))
        overtime = 0.0
        for d in range(1, days_count + 1):
            h = row[str(d)]
            if h > 0:
                if is_weekend(month, d):
                    overtime += h
                elif h > 8:
                    overtime += (h - 8)
        
        row['ИТОГО'] = round(total, 1)
        row['ПЕРЕРАБ'] = round(overtime, 1)
        row['ОТПУСК'] = round(leave_total, 1)
        row['УЧЕБА'] = round(study_total, 1)
        table_data.append(row)

    df_input = pd.DataFrame(table_data)
    column_config = {
        'Сотрудник': st.column_config.TextColumn('Сотрудник', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', disabled=True),
        'ПЕРЕРАБ': st.column_config.NumberColumn('ПЕРЕРАБ', format='%.1f', disabled=True),
        'ОТПУСК': st.column_config.NumberColumn('ОТПУСК', format='%.1f', disabled=True),
        'УЧЕБА': st.column_config.NumberColumn('УЧЕБА', format='%.1f', disabled=True),
    }
    for day in range(1, days_count + 1):
        wd = get_weekday(month, day)
        column_config[str(day)] = st.column_config.NumberColumn(
            f"{day}\n{wd}", min_value=0.0, max_value=24.0, step=0.5, format='%.1f', width='small'
        )

    edited_df = st.data_editor(df_input, column_config=column_config, hide_index=True, use_container_width=True, num_rows='fixed', key='hours_table')

    st.markdown("---")

    if st.button("💾 СОХРАНИТЬ ДАННЫЕ", type="primary", use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                leave_hours = get_leave_hours(month, emp)
                new_hours = []
                total_emp = 0
                for day in range(1, days_count + 1):
                    if day in leave_hours:
                        new_hours.append(0.0)
                    else:
                        try: val = float(edited_df.iloc[idx][str(day)])
                        except: val = 0.0
                        new_hours.append(val)
                        total_emp += val
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                st.session_state.hours_data[f"{month}_{emp}"] = new_hours[:31]
                if total_emp > 0:
                    add_to_feed(f'{emp}: {total_emp:.1f} ч', '⏱')

        ok = save_to_github(get_all_data())
        if ok:
            st.success("✅ ДАННЫЕ СОХРАНЕНЫ В GITHUB!")
            st.balloons()
        else:
            st.error("❌ ОШИБКА СОХРАНЕНИЯ!")
        st.rerun()

    st.markdown("---")
    st.markdown("**📌 Легенда:**  Праздник | 🟠 Сокращённый | 🟣 Выходной |  Отпуск (8ч) | 🔵 Учеба (8ч) | ⚪ Больничный (0ч)")
    st.markdown("💡 **Переработка в выходные** = все часы в выходной день")

# ============================================
# ОТПУСКА, УЧЕБА, БОЛЬНИЧНЫЕ
# ============================================
elif page == "leaves":
    st.title("🏖️ Отпуска, учеба и больничные")
    
    st.markdown("### 📋 Текущие записи")
    if len(st.session_state.leaves) == 0:
        st.info("Нет записей.")
    else:
        leaves_df = pd.DataFrame(st.session_state.leaves)
        leaves_df.columns = ['Сотрудник', 'Тип', 'Начало', 'Конец', 'Дней']
        st.dataframe(leaves_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### ➕ Добавить запись")
    
    col1, col2 = st.columns(2)
    with col1:
        leave_emp = st.selectbox("Сотрудник", EMPLOYEES, key='leave_emp')
    with col2:
        leave_type = st.radio("Тип", ["отпуск", "учеба", "больничный"], horizontal=True, key='leave_type')
    
    col1, col2 = st.columns(2)
    with col1:
        leave_start = st.date_input("Дата начала", value=date(2026, 7, 1), key='leave_start')
    with col2:
        leave_end = st.date_input("Дата конца", value=date(2026, 7, 14), key='leave_end')
    
    if leave_start > leave_end:
        st.error("❌ Дата начала не может быть позже даты конца!")
    else:
        days_count = (leave_end - leave_start).days + 1
        st.info(f"📅 Количество дней: **{days_count}**")
        
        if leave_type == 'отпуск':
            st.info(f"💰 Будет добавлено: **8 часов × рабочие дни** (оплата по среднему)")
        elif leave_type == 'учеба':
            st.info(f"📚 Будет добавлено: **8 часов × рабочие дни** (оплата по среднему)")
        else:
            st.info(f"🏥 Больничный: **0 часов** (не оплачивается)")
        
        if st.button("➕ Добавить", type="primary", use_container_width=True):
            new_leave = {
                'emp': leave_emp,
                'type': leave_type,
                'start': leave_start.strftime('%Y-%m-%d'),
                'end': leave_end.strftime('%Y-%m-%d'),
                'days': days_count
            }
            st.session_state.leaves.append(new_leave)
            
            emoji = '🏖️' if leave_type == 'отпуск' else ('📚' if leave_type == 'учеба' else '🏥')
            add_to_feed(f'{leave_emp}: {leave_type} с {leave_start.strftime("%d.%m")} по {leave_end.strftime("%d.%m")} ({days_count} дн.)', emoji)
            
            ok = save_to_github(get_all_data())
            if ok:
                st.success(f"✅ Добавлено: {leave_emp} - {leave_type} ({days_count} дн.)")
            else:
                st.error("❌ Ошибка сохранения!")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🗑️ Удалить запись")
    
    if len(st.session_state.leaves) > 0:
        delete_options = [f"{l['emp']} - {l['type']} ({l['start']} по {l['end']})" for l in st.session_state.leaves]
        delete_choice = st.selectbox("Выбери запись для удаления", ["— Не удалять —"] + delete_options, key='delete_choice')
        
        if delete_choice != "— Не удалять —":
            if st.button("️ Удалить", type="secondary", use_container_width=True):
                idx = delete_options.index(delete_choice)
                removed = st.session_state.leaves.pop(idx)
                add_to_feed(f'Удалено: {removed["emp"]} - {removed["type"]}', '🗑️')
                save_to_github(get_all_data())
                st.success("✅ Запись удалена!")
                st.rerun()

# ============================================
# ДАШБОРД
# ============================================
elif page == "dashboard":
    st.title(f"📊 Дашборд - {month} 2026")

    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days, leave_count = calc_stats(hours, norm, workdays, month, emp)
        stats_list.append({
            'Сотрудник': emp,
            'Отработано часов': total,
            'Норма часов': norm,
            'Осталось часов': remaining_hours,
            '% выполнения': f'{efficiency:.1f}%',
            'Отработано дней': workdays_worked,
            'Дней отпуска/учебы': leave_count,
            'Переработка': overtime
        })

    df = pd.DataFrame(stats_list)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(" Часы vs Норма")
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
        st.metric("🔥 Всего переработок", f"{df['Переработка'].sum():.1f} ч")
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
                st.subheader("💪 Самый работящий")
                hw = st.radio("Выбери:", [e for e in EMPLOYEES if e != voter], key='hw')
                if st.button("Голосовать за работящего", key='btn_hw'):
                    st.session_state.votes['hardworker'][voter] = hw
                    st.session_state.votes['voters'].append(voter)
                    add_to_feed(f'Голосование: {voter} выбрал работягу', '🗳️')
                    save_to_github(get_all_data())
                    st.success("✅ Голос засчитан анонимно!")
                    st.rerun()
            with col2:
                st.subheader("😴 Главный халявщик")
                sl = st.radio("Выбери:", [e for e in EMPLOYEES if e != voter], key='sl')
                if st.button("Голосовать за халявщика", key='btn_sl'):
                    st.session_state.votes['slacker'][voter] = sl
                    if voter not in st.session_state.votes['voters']:
                        st.session_state.votes['voters'].append(voter)
                    add_to_feed(f'Голосование: {voter} выбрал халявщика', '🗳️')
                    save_to_github(get_all_data())
                    st.success("✅ Голос засчитан анонимно!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📊 Результаты")
    hw_votes = {e: sum(1 for v in st.session_state.votes['hardworker'].values() if v == e) for e in EMPLOYEES}
    sl_votes = {e: sum(1 for v in st.session_state.votes['slacker'].values() if v == e) for e in EMPLOYEES}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💪 Работящий недели:**")
        for e, v in sorted(hw_votes.items(), key=lambda x: x[1], reverse=True):
            if v > 0: st.write(f"{e}: {'█' * v} ({v})")
    with col2:
        st.markdown("**😴 Халявщик недели:**")
        for e, v in sorted(sl_votes.items(), key=lambda x: x[1], reverse=True):
            if v > 0: st.write(f"{e}: {'█' * v} ({v})")

    if st.button("🔄 Новое голосование"):
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        add_to_feed('Начато новое голосование', '️')
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
        total, overtime, efficiency, *_ = calc_stats(hours, norm, workdays, month, emp)
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
                st.markdown(f'<div style="background:#C0C0C0;padding:20px;border-radius:10px;text-align:center;"><h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3><p><b>{df.iloc[1]["Часы"]:.1f} ч</b></p><p>Переработка: {df.iloc[1]["Переработка"]:.1f} ч</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="background:linear-gradient(135deg,#FFD700,#FFA500);padding:30px;border-radius:10px;text-align:center;border:3px solid gold;"><h1>🥇</h1><h2>{df.iloc[0]["Сотрудник"]}</h2><p style="font-size:24px;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p><p style="color:#000;font-size:20px;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p><p>Переработка: {df.iloc[0]["Переработка"]:.1f} ч</p></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div style="background:#CD7F32;padding:20px;border-radius:10px;text-align:center;"><h2>🥉</h2><h3>{df.iloc[2]["Сотрудник"]}</h3><p><b>{df.iloc[2]["Часы"]:.1f} ч</b></p><p>Переработка: {df.iloc[2]["Переработка"]:.1f} ч</p></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Полный рейтинг")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("🏅 Награды месяца")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div style="background:linear-gradient(135deg,#FFD700,#FFA500);padding:20px;border-radius:10px;border:2px solid gold;"><h2>🏆 ГРАМОТА</h2><h3 style="color:#000;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3><p><b>{df.iloc[0]["Сотрудник"]}</b></p><p>{df.iloc[0]["Часы"]:.1f} часов | {df.iloc[0]["Переработка"]:.1f} ч переработки</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="background:linear-gradient(135deg,#8B4513,#654321);padding:20px;border-radius:10px;border:2px solid #8B4513;"><h2>📜 АНТИНАГРАДА</h2><h3 style="color:#FFD700;">ЛОХ</h3><p><b>{df.iloc[-1]["Сотрудник"]}</b></p><p>{df.iloc[-1]["Часы"]:.1f} часов | эффективность {df.iloc[-1]["Эффективность %"]:.0f}%</p></div>', unsafe_allow_html=True)
