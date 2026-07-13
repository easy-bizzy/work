import streamlit as st
import pandas as pd
import json
from datetime import date, datetime
import requests

st.set_page_config(
    page_title="Учёт рабочего времени",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# НАСТРОЙКИ JSONBIN
# ============================================
API_KEY = "$2a$10$fdP3BAMcCh8G0kJpVurg7.fqWCvq9jsXK.yzOcd0ynCzs4H2PEoVC"
BIN_ID = "6a550654da38895dfe578dd3"

# ============================================
# ФУНКЦИИ ОБЛАКА
# ============================================
def load_from_cloud():
    try:
        headers = {'X-Master-Key': API_KEY}
        url = f'https://api.jsonbin.io/v3/b/{BIN_ID}/latest'
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'record' in data:
                return data['record'], "✅ Загружено из облака"
            else:
                return None, "⚠️ Бин пустой"
        else:
            return None, f"❌ Ошибка {response.status_code}"
    except Exception as e:
        return None, f" {e}"

def save_to_cloud(data):
    try:
        headers = {'X-Master-Key': API_KEY, 'Content-Type': 'application/json'}
        url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return True, "✅ Сохранено в облако"
        else:
            return False, f"❌ Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"❌ {e}"

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
# ИНИЦИАЛИЗАЦИЯ (ТОЛЬКО ПЕРВЫЙ РАЗ!)
# ============================================
if 'hours_data' not in st.session_state:
    # Пытаемся загрузить из облака только при первом запуске
    cloud_data, cloud_msg = load_from_cloud()
    
    if cloud_data:
        st.session_state.hours_data = cloud_data.get('hours', {})
        st.session_state.feed = cloud_data.get('feed', [])
        st.session_state.votes = cloud_data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
        st.session_state.checkins = cloud_data.get('checkins', {})
        st.session_state.locked_data = cloud_data.get('locked', {})
        st.session_state.cloud_status = cloud_msg
    else:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.checkins = {}
        st.session_state.locked_data = {}
        st.session_state.cloud_status = cloud_msg

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================
def get_hours(month, emp):
    key = f"{month}_{emp}"
    if key not in st.session_state.hours_data:
        st.session_state.hours_data[key] = [0.0] * 31
    return st.session_state.hours_data[key]

def save_hours(month, emp, hours):
    st.session_state.hours_data[f"{month}_{emp}"] = hours

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

def get_checkin_streak(emp):
    if emp not in st.session_state.checkins:
        return 0
    return len(st.session_state.checkins[emp])

def mark_checkin(emp, month, day):
    if emp not in st.session_state.checkins:
        st.session_state.checkins[emp] = []
    entry = f"{month} День {day} ({date.today().strftime('%d.%m')})"
    if entry not in st.session_state.checkins[emp]:
        st.session_state.checkins[emp].append(entry)

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
st.sidebar.title('📊 Учет рабочего времени')

st.sidebar.markdown('### ☁️ Статус')
st.sidebar.info(st.session_state.cloud_status)
st.sidebar.markdown(f'**Bin ID:** `{BIN_ID}`')

if st.sidebar.button('🔍 Проверить связь', use_container_width=True):
    with st.spinner('Проверка...'):
        data, msg = load_from_cloud()
        if data:
            hours_count = len(data.get('hours', {}))
            st.sidebar.success(f"✅ Связь есть! Записей: {hours_count}")
        else:
            st.sidebar.error(f"❌ {msg}")

if st.sidebar.button('💾 Сохранить сейчас', type='primary', use_container_width=True):
    with st.spinner('Сохранение...'):
        ok, msg = save_to_cloud(get_all_data())
        st.session_state.cloud_status = msg
        if ok:
            st.sidebar.success("✅ Сохранено!")
            st.success("Данные сохранены в облако!")
        else:
            st.sidebar.error(f"❌ {msg}")

if st.sidebar.button('🔄 Загрузить из облака', use_container_width=True):
    with st.spinner('Загрузка...'):
        data, msg = load_from_cloud()
        if data:
            st.session_state.hours_data = data.get('hours', {})
            st.session_state.feed = data.get('feed', [])
            st.session_state.votes = data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
            st.session_state.checkins = data.get('checkins', {})
            st.session_state.locked_data = data.get('locked', {})
            st.session_state.cloud_status = msg
            st.sidebar.success("✅ Загружено!")
            st.success("Данные загружены из облака!")
            st.rerun()
        else:
            st.sidebar.error(f"❌ {msg}")

st.sidebar.markdown('---')

with st.sidebar.expander('🔍 Что сейчас в памяти'):
    st.write(f"**Записей часов:** {len(st.session_state.hours_data)}")
    if st.session_state.hours_data:
        for key in list(st.session_state.hours_data.keys())[:5]:
            hours = st.session_state.hours_data[key]
            total = sum(hours)
            st.write(f"- {key}: {total:.1f} ч")

st.sidebar.markdown('---')

page = st.sidebar.radio('Меню', ['dashboard', 'input', 'activity', 'votes', 'rating'])
month = st.sidebar.selectbox(' Месяц', MONTHS)

month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

st.sidebar.markdown('---')
st.sidebar.markdown(f'**📅 {month} 2026**')
st.sidebar.markdown(f'Рабочих дней: **{workdays}**')
st.sidebar.markdown(f'Норма часов: **{norm}**')

# ============================================
# ВВОД ЧАСОВ
# ============================================
if page == 'input':
    st.title(f'️ Ввод часов — {month} 2026')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info(f' Рабочих дней: **{workdays}**')
    with col2: st.info(f' Норма часов: **{norm}**')
    with col3: st.info(f'🔴 Праздников: **{len(month_info["holidays"])}**')
    with col4: st.info(f'🟠 Сокращённых: **{len(month_info["short"])}**')
    
    st.markdown('---')
    
    cal = month_info
    days_count = DAYS_IN_MONTH[month]
    
    # CSS для окраски колонок таблицы
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
    
    css_string = '\n'.join(css_rules)
    st.markdown(f'<style>{css_string}</style>', unsafe_allow_html=True)
    
    st.markdown('**📅 Календарь месяца (цветные ячейки = выходные/праздники/сокращённые):**')
    
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 15px;">'
    for day in range(1, days_count + 1):
        if day in cal['holidays']:
            color, text_color, label = '#FCA5A5', '#991B1B', f'🔴{day}'
        elif day in cal['short']:
            color, text_color, label = '#FED7AA', '#9A3412', f'🟠{day}'
        elif day in cal['weekends']:
            color, text_color, label = '#E9D5FF', '#6B21A8', f'{day}'
        else:
            color, text_color, label = '#374151', '#FFFFFF', str(day)
        
        legend_html += f'<div style="background-color: {color}; color: {text_color}; padding: 4px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; min-width: 28px; text-align: center;">{label}</div>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)
    
    # Таблица
    table_data = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        row = {'Сотрудник': emp}
        
        for day in range(1, days_count + 1):
            h = float(hours[day-1]) if day-1 < len(hours) else 0.0
            row[str(day)] = h
        
        total = sum(row[str(day)] for day in range(1, days_count + 1))
        overtime = sum(max(0, row[str(day)] - 8) for day in range(1, days_count + 1) if row[str(day)] > 0)
        row['ИТОГО'] = round(total, 1)
        row['ПЕРЕРАБ'] = round(overtime, 1)
        
        table_data.append(row)
    
    df_input = pd.DataFrame(table_data)
    
    column_config = {
        'Сотрудник': st.column_config.TextColumn('Сотрудник', width='medium', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', width='small', disabled=True),
        'ПЕРЕРАБ': st.column_config.NumberColumn('ПЕРЕРАБ', format='%.1f', width='small', disabled=True),
    }
    
    for day in range(1, days_count + 1):
        if day in cal['holidays']:
            day_label = f'🔴{day}'
        elif day in cal['short']:
            day_label = f'🟠{day}'
        elif day in cal['weekends']:
            day_label = f'🟣{day}'
        else:
            day_label = str(day)
        
        column_config[str(day)] = st.column_config.NumberColumn(
            day_label,
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            format='%.1f',
            width='small'
        )
    
    st.markdown('**💡 Кликай на ячейку и вводи часы. После сохранения данные улетят в облако!**')
    
    edited_df = st.data_editor(
        df_input,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows='fixed',
        key='hours_table'
    )
    
    for idx in range(len(edited_df)):
        total = sum(float(edited_df.iloc[idx][str(day)]) for day in range(1, days_count + 1))
        overtime = sum(max(0, float(edited_df.iloc[idx][str(day)]) - 8) 
                      for day in range(1, days_count + 1) 
                      if float(edited_df.iloc[idx][str(day)]) > 0)
        edited_df.at[edited_df.index[idx], 'ИТОГО'] = round(total, 1)
        edited_df.at[edited_df.index[idx], 'ПЕРЕРАБ'] = round(overtime, 1)
    
    st.markdown('---')
    
    if st.button('💾 СОХРАНИТЬ В ОБЛАКО И ЗАФИКСИРОВАТЬ', type='primary', use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df) and not is_locked(month, emp):
                new_hours = []
                total_emp = 0
                days_worked = 0
                for day in range(1, days_count + 1):
                    val = edited_df.iloc[idx][str(day)]
                    try:
                        val = float(val)
                    except:
                        val = 0.0
                    new_hours.append(val)
                    total_emp += val
                    if val > 0:
                        days_worked += 1
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                save_hours(month, emp, new_hours[:31])
                lock_data(month, emp)
                
                if total_emp > 0:
                    add_to_feed(
                        f'{emp} проставил часы за {month}: {total_emp:.1f} ч ({days_worked} дн.) 🔒',
                        '⏱'
                    )
                    mark_checkin(emp, month, days_worked)
        
        ok, msg = save_to_cloud(get_all_data())
        st.session_state.cloud_status = msg
        
        if ok:
            st.success('✅ Данные сохранены в облако и ЗАФИКСИРОВАНЫ!')
            st.balloons()
        else:
            st.error(f'❌ Ошибка: {msg}')
        
        st.rerun()
    
    st.markdown('---')
    st.markdown('**🔒 Статус блокировки:**')
    for emp in EMPLOYEES:
        if is_locked(month, emp):
            st.success(f'✅ {emp} — данные зафиксированы 🔒')
        else:
            st.warning(f'️ {emp} — можно редактировать')
    
    st.markdown('---')
    st.markdown('**📌 Легенда:**')
    st.markdown('''
    <span style="background-color: #FCA5A5; color: #991B1B; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">🔴 Праздник</span>
    <span style="background-color: #FED7AA; color: #9A3412; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">🟠 Сокращённый</span>
    <span style="background-color: #E9D5FF; color: #6B21A8; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">🟣 Выходной</span>
    <span style="background-color: #374151; color: white; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">⚪ Рабочий</span>
    ''', unsafe_allow_html=True)
    st.markdown('💡 **Переработка** = всё что больше 8 часов в день')

# ============================================
# ДАШБОРД
# ============================================
elif page == 'dashboard':
    st.title(f'📊 Дашборд — {month} 2026')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days = calc_stats(hours, norm, workdays)
        streak = get_checkin_streak(emp)
        locked_status = '🔒' if is_locked(month, emp) else '🔓'
        stats_list.append({
            'Сотрудник': f'{locked_status} {emp}',
            'Отработано часов': total,
            'Норма часов': norm,
            'Осталось часов': remaining_hours,
            'Процент выполнения': f'{efficiency:.1f}%',
            'Отработано дней': workdays_worked,
            'Рабочих дней в месяце': workdays,
            'Осталось дней': remaining_days,
            'Переработка': overtime,
            'Серия дней 🔥': streak
        })
    
    df = pd.DataFrame(stats_list)
    
    st.subheader('📋 Статистика по каждому сотруднику')
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown('---')
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('⏱ Отработанные часы vs Норма')
        if not df.empty:
            st.bar_chart(df.set_index('Сотрудник')[['Отработано часов', 'Норма часов']])
    with col2:
        st.subheader('🔥 Переработка по сотрудникам')
        if not df.empty:
            st.bar_chart(df.set_index('Сотрудник')['Переработка'])
    
    st.markdown('---')
    st.subheader('📈 Статистика')
    col1, col2, col3 = st.columns(3)
    with col1:
        top_worker = df.loc[df['Отработано часов'].idxmax()]
        st.metric(' Лидер месяца', top_worker['Сотрудник'], f"{top_worker['Отработано часов']:.1f} ч")
    with col2:
        st.metric('🔥 Всего переработок', f"{df['Переработка'].sum():.1f} ч")
    with col3:
        completed = len(df[df['Осталось часов'] == 0])
        st.metric('✅ Выполнили норму', f'{completed} чел.')
    
    st.markdown('---')
    st.subheader('📊 Детальная статистика по сотрудникам')
    
    df_sorted = df.sort_values('Отработано часов', ascending=False).reset_index(drop=True)
    leader_name = df_sorted.iloc[0]['Сотрудник'] if len(df_sorted) > 0 else None
    
    for idx, row in df_sorted.iterrows():
        emp = row['Сотрудник']
        is_leader = (emp == leader_name) and row['Отработано часов'] > 0
        
        if is_leader:
            st.markdown(f'### 🏆 {emp} — ЛИДЕР МЕСЯЦА')
        else:
            st.markdown(f'### #{idx + 1} {emp}')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(' Всего часов', f"{row['Отработано часов']:.1f} / {norm}")
        with col2:
            st.metric('📅 Рабочих дней', f"{row['Отработано дней']} / {workdays}")
        with col3:
            st.metric('🔥 Переработка', f"{row['Переработка']:.1f} ч")
        with col4:
            remaining = row['Осталось часов']
            if remaining > 0:
                st.metric(' Осталось часов', f"{remaining:.1f} ч")
            else:
                st.metric('✅ Норма выполнена', f"+{row['Отработано часов'] - norm:.1f} ч")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**📊 % выполнения по часам:** {row['Процент выполнения']}")
        with col2:
            days_percent = (row['Отработано дней'] / workdays * 100) if workdays > 0 else 0
            st.markdown(f"**📅 % выполнения по дням:** {days_percent:.1f}%")
        
        hours_percent = float(row['Процент выполнения'].replace('%', ''))
        progress_value = min(hours_percent / 100, 1.0)
        bar_html = f'''
        <div style="background-color: #2d2d2d; border-radius: 10px; padding: 3px; margin: 15px 0;">
            <div style="background-color: #9CA3AF; width: {progress_value * 100}%; height: 35px; border-radius: 8px; text-align: center; line-height: 35px; color: white; font-weight: bold; font-size: 14px;">
                {hours_percent:.1f}%
            </div>
        </div>
        '''
        st.markdown(bar_html, unsafe_allow_html=True)
        st.markdown('---')

# ============================================
# ЛЕНТА АКТИВНОСТИ
# ============================================
elif page == 'activity':
    st.title('📱 Лента активности')
    
    st.markdown('**Здесь отображаются все действия сотрудников в реальном времени**')
    st.markdown('---')
    
    st.subheader('🔥 Ежедневные серии')
    
    checkin_data = []
    for emp in EMPLOYEES:
        streak = get_checkin_streak(emp)
        checkin_data.append({
            'Сотрудник': emp,
            'Серия дней': streak,
            'Статус': '🔥 В игре' if streak > 0 else '😴 Не активен'
        })
    
    df_checkin = pd.DataFrame(checkin_data).sort_values('Серия дней', ascending=False)
    st.dataframe(df_checkin, use_container_width=True, hide_index=True)
    
    st.markdown('---')
    
    st.subheader('📰 Последние события')
    
    if len(st.session_state.feed) == 0:
        st.info(' Лента пуста. Начни вводить часы — события появятся здесь!')
    else:
        for item in st.session_state.feed:
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px;">{item['emoji']} {item['message']}</span>
                    <span style="font-size: 12px; color: #94a3b8;">{item['time']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('---')
    
    if st.button('🗑️ Очистить ленту', use_container_width=True):
        st.session_state.feed = []
        save_to_cloud(get_all_data())
        st.success('Лента очищена!')
        st.rerun()

# ============================================
# ГОЛОСОВАНИЯ
# ============================================
elif page == 'votes':
    st.title('️ Голосования недели')
    
    st.markdown('**Проголосуй анонимно за самого работящего и главного халявщика команды!**')
    st.markdown('🔒 Голосование анонимное — никто не увидит твой выбор')
    st.markdown('---')
    
    voter = st.selectbox('👤 Кто голосует?', ['— Выбери себя —'] + EMPLOYEES)
    
    if voter == '— Выбери себя —':
        st.warning('️ Выбери своё имя чтобы проголосовать')
    else:
        already_voted = voter in st.session_state.votes['voters']
        
        if already_voted:
            st.success('✅ Ты уже проголосовал на этой неделе! Результаты ниже.')
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader('💪 Самый работящий')
                st.markdown('Кто вкалывал больше всех на этой неделе?')
                
                hardworker_choice = st.radio(
                    'Выбери работящего:',
                    [e for e in EMPLOYEES if e != voter],
                    key='hw_vote'
                )
                if st.button('✅ Голосовать за работящего', type='primary', use_container_width=True):
                    st.session_state.votes['hardworker'][voter] = hardworker_choice
                    st.session_state.votes['voters'].append(voter)
                    add_to_feed(f'Проведено анонимное голосование за работящего недели 💪', '🗳️')
                    save_to_cloud(get_all_data())
                    st.success('✅ Голос засчитан анонимно!')
                    st.rerun()
            
            with col2:
                st.subheader('😴 Главный халявщик')
                st.markdown('Кто больше всех проебался на этой неделе?')
                
                slacker_choice = st.radio(
                    'Выбери халявщика:',
                    [e for e in EMPLOYEES if e != voter],
                    key='sl_vote'
                )
                if st.button('🗳️ Голосовать за халявщика', type='primary', use_container_width=True):
                    st.session_state.votes['slacker'][voter] = slacker_choice
                    if voter not in st.session_state.votes['voters']:
                        st.session_state.votes['voters'].append(voter)
                    add_to_feed(f'Проведено анонимное голосование за халявщика недели 😴', '🗳️')
                    save_to_cloud(get_all_data())
                    st.success('✅ Голос засчитан анонимно!')
                    st.rerun()
    
    st.markdown('---')
    
    st.subheader('📊 Результаты голосования')
    
    hw_votes = {}
    sl_votes = {}
    for emp in EMPLOYEES:
        hw_votes[emp] = sum(1 for v in st.session_state.votes['hardworker'].values() if v == emp)
        sl_votes[emp] = sum(1 for v in st.session_state.votes['slacker'].values() if v == emp)
    
    total_voters = len(st.session_state.votes['voters'])
    st.markdown(f'**Проголосовало человек:** {total_voters} из {len(EMPLOYEES)}')
    
    st.markdown('---')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('### 💪 Работящий недели')
        hw_df = pd.DataFrame([
            {'Сотрудник': emp, 'Голоса': hw_votes[emp]} 
            for emp in EMPLOYEES
        ]).sort_values('Голоса', ascending=False)
        
        for idx, row in hw_df.iterrows():
            if row['Голоса'] > 0:
                bar = '█' * row['Голоса']
                st.markdown(f'**{row["Сотрудник"]}**: {bar} ({row["Голоса"]})')
            else:
                st.markdown(f'{row["Сотрудник"]}: 0')
    
    with col2:
        st.markdown('### 😴 Халявщик недели')
        sl_df = pd.DataFrame([
            {'Сотрудник': emp, 'Голоса': sl_votes[emp]} 
            for emp in EMPLOYEES
        ]).sort_values('Голоса', ascending=False)
        
        for idx, row in sl_df.iterrows():
            if row['Голоса'] > 0:
                bar = '█' * row['Голоса']
                st.markdown(f'**{row["Сотрудник"]}**: {bar} ({row["Голоса"]})')
            else:
                st.markdown(f'{row["Сотрудник"]}: 0')
    
    st.markdown('---')
    
    top_hw = max(hw_votes, key=hw_votes.get) if any(v > 0 for v in hw_votes.values()) else None
    top_sl = max(sl_votes, key=sl_votes.get) if any(v > 0 for v in sl_votes.values()) else None
    
    if top_hw or top_sl:
        st.subheader('🏆 Лидеры голосования')
        col1, col2 = st.columns(2)
        
        if top_hw and hw_votes[top_hw] > 0:
            with col1:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #10b981, #059669); padding:20px; border-radius:10px; text-align:center;">
                <h2>💪 РАБОТЯГА НЕДЕЛИ</h2>
                <h3>{top_hw}</h3>
                <p>{hw_votes[top_hw]} голос(ов)</p>
                </div>
                """, unsafe_allow_html=True)
        
        if top_sl and sl_votes[top_sl] > 0:
            with col2:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #ef4444, #dc2626); padding:20px; border-radius:10px; text-align:center;">
                <h2>😴 ХАЛЯВЩИК НЕДЕЛИ</h2>
                <h3>{top_sl}</h3>
                <p>{sl_votes[top_sl]} голос(ов)</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('---')
    
    if st.button('🔄 Начать новое голосование', use_container_width=True):
        st.session_state.votes = {
            'hardworker': {},
            'slacker': {},
            'voters': []
        }
        add_to_feed('🔄 Начато новое голосование недели!', '️')
        save_to_cloud(get_all_data())
        st.success('Голосование сброшено!')
        st.rerun()

# ============================================
# РЕЙТИНГ
# ============================================
elif page == 'rating':
    st.title(f'🏆 Рейтинг — {month}')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days = calc_stats(hours, norm, workdays)
        stats_list.append({
            'Сотрудник': emp,
            'Часы': total,
            'Переработка': overtime,
            'Эффективность %': round(efficiency, 1)
        })
    
    df = pd.DataFrame(stats_list).sort_values('Часы', ascending=False).reset_index(drop=True)
    
    if df['Часы'].sum() == 0:
        st.warning('⚠️ Нет данных за этот месяц. Введите часы на странице "Ввод часов".')
    else:
        st.markdown('---')
        st.subheader('🏆 Подиум')
        
        if len(df) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;">
                <h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3>
                <p><b>{df.iloc[1]["Часы"]:.1f} ч</b></p>
                <p>Переработка: {df.iloc[1]["Переработка"]:.1f} ч</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:30px; border-radius:10px; text-align:center; border:3px solid gold;">
                <h1>🥇</h1><h2>{df.iloc[0]["Сотрудник"]}</h2>
                <p style="font-size:24px;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p>
                <p>Переработка: {df.iloc[0]["Переработка"]:.1f} ч</p>
                <p style="font-size:20px; color:#000;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background:#CD7F32; padding:20px; border-radius:10px; text-align:center;">
                <h2></h2><h3>{df.iloc[2]["Сотрудник"]}</h3>
                <p><b>{df.iloc[2]["Часы"]:.1f} ч</b></p>
                <p>Переработка: {df.iloc[2]["Переработка"]:.1f} ч</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('---')
        st.subheader(' Полный рейтинг')
        st.dataframe(df, use_container_width=True)
        
        st.markdown('---')
        st.subheader('🏅 Награды месяца')
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:20px; border-radius:10px; border:2px solid gold;">
            <h2>🏆 ГРАМОТА</h2><h3 style="color:#000;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3>
            <p><b>{df.iloc[0]["Сотрудник"]}</b></p>
            <p>{df.iloc[0]["Часы"]:.1f} часов | {df.iloc[0]["Переработка"]:.1f} ч переработки</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #8B4513, #654321); padding:20px; border-radius:10px; border:2px solid #8B4513;">
            <h2> АНТИНАГРАДА</h2><h3 style="color:#FFD700;">ЛОХ</h3>
            <p><b>{df.iloc[-1]["Сотрудник"]}</b></p>
            <p>{df.iloc[-1]["Часы"]:.1f} часов | эффективность {df.iloc[-1]["Эффективность %"]:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
