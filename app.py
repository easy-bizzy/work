import streamlit as st
import pandas as pd
import json
from datetime import date, datetime
import requests

st.set_page_config(page_title="Учёт рабочего времени", page_icon="📊", layout="wide")

# ============================================
# НАСТРОЙКИ JSONBIN
# ============================================
API_KEY = "$2a$10$fdP3BAMcCh8G0kJpVurg7.fqWCvq9jsXK.yzOcd0ynCzs4H2PEoVC"
BIN_ID = "6a53ccceda38895dfe534f3f"

# ============================================
# ФУНКЦИИ С ПОДРОБНОЙ ДИАГНОСТИКОЙ
# ============================================
def load_from_cloud():
    """Загрузка с полной диагностикой"""
    try:
        headers = {'X-Master-Key': API_KEY}
        url = f'https://api.jsonbin.io/v3/b/{BIN_ID}/latest'
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📥 GET запрос: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'record' in data:
                record = data['record']
                hours_count = len(record.get('hours', {}))
                print(f"✅ Загружено записей часов: {hours_count}")
                return record, f"✅ Загружено {hours_count} записей"
            else:
                print(f"⚠️ Нет поля 'record' в ответе")
                return None, "⚠️ Нет данных в бине"
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            return None, f"❌ Ошибка {response.status_code}"
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return None, f"❌ {e}"

def save_to_cloud(data):
    """Сохранение с полной диагностикой"""
    try:
        headers = {'X-Master-Key': API_KEY, 'Content-Type': 'application/json'}
        url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
        
        data_json = json.dumps(data, ensure_ascii=False)
        print(f"📤 PUT запрос, размер: {len(data_json)} байт")
        print(f"📊 Записей часов: {len(data.get('hours', {}))}")
        
        response = requests.put(url, headers=headers, json=data, timeout=10)
        print(f"📥 Ответ: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Сохранено успешно")
            return True, "✅ Сохранено"
        else:
            print(f"❌ Ошибка сохранения: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False, f"❌ Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        print(f"❌ Исключение при сохранении: {e}")
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
# ЗАГРУЗКА ПРИ СТАРТЕ (ВСЕГДА)
# ============================================
print("\n" + "="*50)
print(" ЗАПУСК ПРИЛОЖЕНИЯ")
print("="*50)

cloud_data, cloud_msg = load_from_cloud()

if cloud_data:
    st.session_state.hours_data = cloud_data.get('hours', {})
    st.session_state.feed = cloud_data.get('feed', [])
    st.session_state.votes = cloud_data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
    st.session_state.checkins = cloud_data.get('checkins', {})
    st.session_state.locked_data = cloud_data.get('locked', {})
    st.session_state.cloud_status = cloud_msg
    print(f"✅ Данные загружены в session_state")
else:
    if 'hours_data' not in st.session_state:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.checkins = {}
        st.session_state.locked_data = {}
    st.session_state.cloud_status = cloud_msg
    print(f"⚠️ Данные не загружены: {cloud_msg}")

print("="*50 + "\n")

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

# Показать что сейчас в памяти
with st.sidebar.expander('🔍 Что в памяти сейчас'):
    st.write(f"**Записей часов:** {len(st.session_state.hours_data)}")
    if st.session_state.hours_data:
        for key in list(st.session_state.hours_data.keys())[:3]:
            st.write(f"- {key}")

# Кнопка сохранения
if st.sidebar.button('💾 СОХРАНИТЬ В ОБЛАКО', type='primary', use_container_width=True):
    with st.spinner('Сохранение...'):
        data = get_all_data()
        ok, msg = save_to_cloud(data)
        st.session_state.cloud_status = msg
        if ok:
            st.sidebar.success("✅ Сохранено!")
            st.success("Данные сохранены в облако!")
        else:
            st.sidebar.error(f" {msg}")
            st.error(f"Ошибка: {msg}")

# Кнопка загрузки
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

# Прямая ссылка на бин
st.sidebar.markdown(f'**Bin ID:** `{BIN_ID}`')
st.sidebar.markdown(f'[🔗 Открыть в JSONBin](https://jsonbin.io/b/{BIN_ID})')

st.sidebar.markdown('---')
page = st.sidebar.radio('Меню', ['dashboard', 'input', 'activity', 'votes', 'rating'])
month = st.sidebar.selectbox(' Месяц', MONTHS)
month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

# ============================================
# ВВОД ЧАСОВ
# ============================================
if page == 'input':
    st.title(f'⏱️ Ввод часов — {month} 2026')
    
    cal = month_info
    days_count = DAYS_IN_MONTH[month]
    
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
        'Сотрудник': st.column_config.TextColumn('Сотрудник', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', disabled=True),
        'ПЕРЕРАБ': st.column_config.NumberColumn('ПЕРЕРАБ', format='%.1f', disabled=True),
    }
    for day in range(1, days_count + 1):
        column_config[str(day)] = st.column_config.NumberColumn(str(day), min_value=0.0, max_value=24.0, step=0.5, format='%.1f', width='small')
    
    edited_df = st.data_editor(df_input, column_config=column_config, hide_index=True, use_container_width=True, num_rows='fixed', key='hours_table')
    
    if st.button('💾 СОХРАНИТЬ И ЗАФИКСИРОВАТЬ', type='primary', use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df) and not is_locked(month, emp):
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
                save_hours(month, emp, new_hours[:31])
                lock_data(month, emp)
                if total_emp > 0:
                    add_to_feed(f'{emp}: {total_emp:.1f} ч 🔒', '⏱')
        
        # СОХРАНЯЕМ
        data = get_all_data()
        print(f"\n💾 Сохраняем данные:")
        print(f"   Записей часов: {len(data['hours'])}")
        print(f"   Пример: {list(data['hours'].items())[:2]}")
        
        ok, msg = save_to_cloud(data)
        st.session_state.cloud_status = msg
        
        if ok:
            st.success('✅ Данные сохранены в облако и ЗАФИКСИРОВАНЫ!')
            st.balloons()
        else:
            st.error(f'❌ Ошибка: {msg}')
        
        st.rerun()

    st.markdown('**🔒 Статус блокировки:**')
    for emp in EMPLOYEES:
        if is_locked(month, emp):
            st.success(f'✅ {emp} — зафиксировано 🔒')
        else:
            st.warning(f'⚠️ {emp} — можно редактировать')

# ============================================
# ОСТАЛЬНЫЕ СТРАНИЦЫ (упрощённо)
# ============================================
elif page == 'dashboard':
    st.title(f' Дашборд — {month} 2026')
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

elif page == 'activity':
    st.title('📱 Лента активности')
    if len(st.session_state.feed) == 0:
        st.info(' Лента пуста.')
    else:
        for item in st.session_state.feed:
            st.markdown(f"**{item['time']}** {item['emoji']} {item['message']}")

elif page == 'votes':
    st.title('🗳️ Голосования')
    voter = st.selectbox('👤 Кто голосует?', ['— Выбери себя —'] + EMPLOYEES)
    if voter != '— Выбери себя —':
        already_voted = voter in st.session_state.votes['voters']
        if already_voted:
            st.success('✅ Ты уже проголосовал!')
        else:
            col1, col2 = st.columns(2)
            with col1:
                hw_choice = st.radio(' Работящий:', [e for e in EMPLOYEES if e != voter], key='hw')
                if st.button('Голосовать за работящего'):
                    st.session_state.votes['hardworker'][voter] = hw_choice
                    st.session_state.votes['voters'].append(voter)
                    save_to_cloud(get_all_data())
                    st.success('✅ Голос засчитан!')
                    st.rerun()
            with col2:
                sl_choice = st.radio('😴 Халявщик:', [e for e in EMPLOYEES if e != voter], key='sl')
                if st.button('Голосовать за халявщика'):
                    st.session_state.votes['slacker'][voter] = sl_choice
                    if voter not in st.session_state.votes['voters']:
                        st.session_state.votes['voters'].append(voter)
                    save_to_cloud(get_all_data())
                    st.success('✅ Голос засчитан!')
                    st.rerun()

elif page == 'rating':
    st.title(f'🏆 Рейтинг — {month}')
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, *_ = calc_stats(hours, norm, workdays)
        stats_list.append({'Сотрудник': emp, 'Часы': total, 'Переработка': overtime, 'Эффективность %': round(efficiency, 1)})
    df = pd.DataFrame(stats_list).sort_values('Часы', ascending=False).reset_index(drop=True)
    st.dataframe(df, use_container_width=True)
