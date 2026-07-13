import streamlit as st
import pandas as pd
import json
from datetime import datetime
import requests

st.set_page_config(page_title="Учёт часов", page_icon="📊", layout="wide")

# ============================================
# НАСТРОЙКИ
# ============================================
API_KEY = "$2a$10$fdP3BAMcCh8G0kJpVurg7.fqWCvq9jsXK.yzOcd0ynCzs4H2PEoVC"
BIN_ID = "6a550654da38895dfe578dd3"

EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']

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
            record = data.get('record', {})
            hours = record.get('hours', {})
            st.sidebar.write(f"Загружено записей: {len(hours)}")
            return record, True
        else:
            st.sidebar.error(f"Ошибка загрузки: {response.status_code}")
            return None, False
    except Exception as e:
        st.sidebar.error(f"Исключение: {e}")
        return None, False

def save_to_cloud(data):
    headers = {'X-Master-Key': API_KEY, 'Content-Type': 'application/json'}
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    try:
        hours_count = len(data.get('hours', {}))
        st.sidebar.write(f"Отправляем записей: {hours_count}")
        response = requests.put(url, headers=headers, json=data, timeout=10)
        st.sidebar.write(f"PUT ответ: {response.status_code}")
        if response.status_code == 200:
            st.sidebar.success("Сохранено успешно!")
            return True
        else:
            st.sidebar.error(f"Ошибка: {response.status_code}")
            st.sidebar.code(response.text[:300])
            return False
    except Exception as e:
        st.sidebar.error(f"Исключение: {e}")
        return False

# ============================================
# ЗАГРУЗКА ДАННЫХ ПРИ СТАРТЕ
# ============================================
st.sidebar.markdown("### Загрузка при старте")
cloud_data, load_ok = load_from_cloud()

if load_ok and cloud_data:
    st.session_state.hours_data = cloud_data.get('hours', {})
    st.session_state.feed = cloud_data.get('feed', [])
    st.session_state.votes = cloud_data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
    st.session_state.checkins = cloud_data.get('checkins', {})
    st.session_state.locked_data = cloud_data.get('locked', {})
    st.sidebar.success(f"Загружено {len(st.session_state.hours_data)} записей")
else:
    if 'hours_data' not in st.session_state:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.checkins = {}
        st.session_state.locked_data = {}
    st.sidebar.warning("Загрузка не удалась, начинаем с нуля")

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
st.sidebar.markdown("---")
st.sidebar.markdown("### Ручное сохранение")

if st.sidebar.button("СОХРАНИТЬ СЕЙЧАС", type="primary", use_container_width=True):
    with st.spinner("Сохранение..."):
        data = get_all_data()
        ok = save_to_cloud(data)
        if ok:
            st.success("Данные сохранены в облако!")
        else:
            st.error("Ошибка сохранения. Смотри диагностику в боковой панели.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Текущее состояние")
st.sidebar.write(f"Записей часов: {len(st.session_state.hours_data)}")
if st.session_state.hours_data:
    for key in list(st.session_state.hours_data.keys())[:5]:
        total = sum(st.session_state.hours_data[key])
        st.sidebar.write(f"- {key}: {total:.1f} ч")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "dashboard"])
month = st.sidebar.selectbox("Месяц", MONTHS)

# ============================================
# ВВОД ЧАСОВ
# ============================================
if page == "input":
    st.title(f"Ввод часов - {month}")
    
    days_count = 31
    if month in ['СЕНТЯБРЬ', 'НОЯБРЬ']:
        days_count = 30
    
    table_data = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        row = {'Сотрудник': emp}
        for day in range(1, days_count + 1):
            row[str(day)] = float(hours[day-1]) if day-1 < len(hours) else 0.0
        row['ИТОГО'] = round(sum(row[str(d)] for d in range(1, days_count + 1)), 1)
        table_data.append(row)
    
    df_input = pd.DataFrame(table_data)
    
    column_config = {
        'Сотрудник': st.column_config.TextColumn('Сотрудник', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', disabled=True),
    }
    for day in range(1, days_count + 1):
        column_config[str(day)] = st.column_config.NumberColumn(
            str(day), min_value=0.0, max_value=24.0, step=0.5, format='%.1f', width='small'
        )
    
    edited_df = st.data_editor(
        df_input,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows='fixed',
        key='hours_table'
    )
    
    st.markdown("---")
    
    if st.button("СОХРАНИТЬ В ОБЛАКО", type="primary", use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                new_hours = []
                for day in range(1, days_count + 1):
                    val = edited_df.iloc[idx][str(day)]
                    try:
                        val = float(val)
                    except:
                        val = 0.0
                    new_hours.append(val)
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                st.session_state.hours_data[f"{month}_{emp}"] = new_hours[:31]
                lock_data(month, emp)
        
        st.write(f"Сохраняем {len(st.session_state.hours_data)} записей:")
        st.write(list(st.session_state.hours_data.keys()))
        
        data = get_all_data()
        ok = save_to_cloud(data)
        
        if ok:
            st.success("ДАННЫЕ СОХРАНЕНЫ В ОБЛАКО!")
            st.balloons()
        else:
            st.error("ОШИБКА СОХРАНЕНИЯ! Смотри боковую панель.")
        
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Статус:**")
    for emp in EMPLOYEES:
        if is_locked(month, emp):
            st.success(f"{emp} - зафиксировано")
        else:
            st.warning(f"{emp} - можно редактировать")

# ============================================
# ДАШБОРД
# ============================================
elif page == "dashboard":
    st.title(f"Дашборд - {month}")
    
    stats = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total = sum(hours)
        stats.append({'Сотрудник': emp, 'Часы': total})
    
    df = pd.DataFrame(stats)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if df['Часы'].sum() > 0:
        st.bar_chart(df.set_index('Сотрудник'))
    else:
        st.info("Нет данных. Введи часы на странице 'input'.")
