import streamlit as st
import pandas as pd
import json
from datetime import datetime
import requests

st.set_page_config(page_title="Учёт часов", page_icon="", layout="wide")

API_KEY = "$2a$10$fdP3BAMcCh8G0kJpVurg7.fqWCvq9jsXK.yzOcd0ynCzs4H2PEoVC"
BIN_ID = "6a550654da38895dfe578dd3"

EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']

DAYS_IN_MONTH = {'ИЮЛЬ': 31, 'АВГУСТ': 31, 'СЕНТЯБРЬ': 30, 'ОКТЯБРЬ': 31, 'НОЯБРЬ': 30, 'ДЕКАБРЬ': 31}

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

# ЗАГРУЗКА ПРИ СТАРТЕ
cloud_data, load_ok = load_from_cloud()
if load_ok and cloud_data:
    st.session_state.hours_data = cloud_data.get('hours', {})
    st.session_state.feed = cloud_data.get('feed', [])
    st.session_state.votes = cloud_data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
    st.session_state.checkins = cloud_data.get('checkins', {})
    st.session_state.locked_data = cloud_data.get('locked', {})
else:
    if 'hours_data' not in st.session_state:
        st.session_state.hours_data = {}
        st.session_state.feed = []
        st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
        st.session_state.checkins = {}
        st.session_state.locked_data = {}

def get_hours(month, emp):
    key = f"{month}_{emp}"
    if key not in st.session_state.hours_data:
        st.session_state.hours_data[key] = [0.0] * 31
    return st.session_state.hours_data[key]

def get_all_data():
    return {
        'hours': st.session_state.hours_data,
        'feed': st.session_state.feed,
        'votes': st.session_state.votes,
        'checkins': st.session_state.checkins,
        'locked': st.session_state.locked_data
    }

# БОКОВАЯ ПАНЕЛЬ
st.sidebar.title("Учёт часов")
st.sidebar.write(f"Записей в памяти: {len(st.session_state.hours_data)}")

if st.sidebar.button("СОХРАНИТЬ В ОБЛАКО", type="primary", use_container_width=True):
    with st.spinner("Сохранение..."):
        ok = save_to_cloud(get_all_data())
        if ok:
            st.sidebar.success("✅ Сохранено!")
            st.success("Данные сохранены в облако!")
        else:
            st.sidebar.error("❌ Ошибка!")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "dashboard"])
month = st.sidebar.selectbox("Месяц", MONTHS)

# ВВОД ЧАСОВ
if page == "input":
    st.title(f"Ввод часов - {month}")
    
    days_count = DAYS_IN_MONTH[month]
    
    # Показываем текущие данные
    st.markdown("### Текущие данные в памяти:")
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total = sum(hours)
        if total > 0:
            st.write(f"- {emp}: {total:.1f} ч")
    
    st.markdown("---")
    
    # Таблица для ввода
    table_data = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        row = {'Сотрудник': emp}
        for day in range(1, days_count + 1):
            row[str(day)] = float(hours[day-1]) if day-1 < len(hours) else 0.0
        table_data.append(row)
    
    df_input = pd.DataFrame(table_data)
    
    column_config = {
        'Сотрудник': st.column_config.TextColumn('Сотрудник', disabled=True),
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
    
    # Кнопка сохранения с диагностикой
    if st.button("СОХРАНИТЬ ДАННЫЕ ИЗ ТАБЛИЦЫ", type="primary", use_container_width=True):
        st.write("### Сохраняем данные...")
        
        saved_count = 0
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
                
                # Сохраняем в session_state
                key = f"{month}_{emp}"
                st.session_state.hours_data[key] = new_hours[:31]
                saved_count += 1
                
                total = sum(new_hours[:31])
                st.write(f"✅ {emp}: {total:.1f} ч сохранено")
        
        st.write(f"\n**Всего сохранено записей: {saved_count}**")
        st.write(f"**Всего записей в памяти: {len(st.session_state.hours_data)}**")
        
        # Сохраняем в облако
        ok = save_to_cloud(get_all_data())
        
        if ok:
            st.success("✅ ДАННЫЕ СОХРАНЕНЫ В ОБЛАКО!")
            st.balloons()
        else:
            st.error(" ОШИБКА СОХРАНЕНИЯ В ОБЛАКО!")
        
        st.rerun()

# ДАШБОРД
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
