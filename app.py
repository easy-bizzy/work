import streamlit as st
import pandas as pd
import requests
import base64
import json
import os
from datetime import datetime

st.set_page_config(page_title="Учёт часов", page_icon="", layout="wide")

# НАСТРОЙКИ — токен берётся из Streamlit Secrets
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_OWNER = "easy-bizzy"
REPO_NAME = "work"
FILE_PATH = "data.json"

# Диагностика токена
if not GITHUB_TOKEN:
    st.error("❌ Токен не найден! Добавь его в Streamlit Secrets.")
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
        elif r.status_code == 401:
            st.sidebar.error("❌ Неверный токен! Проверь Secrets.")
            return None, False
        elif r.status_code == 404:
            st.sidebar.error("❌ Файл data.json не найден в репозитории!")
            return None, False
        else:
            st.sidebar.error(f"❌ Ошибка {r.status_code}")
            return None, False
    except Exception as e:
        st.sidebar.error(f"❌ {e}")
        return None, False

def save_to_github(data):
    try:
        r = requests.get(get_file_url(), headers=get_headers(), timeout=10)
        sha = r.json()['sha'] if r.status_code == 200 else None
        
        content = json.dumps(data, ensure_ascii=False, indent=2)
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        payload = {"message": f"Update {datetime.now().strftime('%H:%M:%S')}", 
                   "content": encoded, "branch": "main"}
        if sha:
            payload["sha"] = sha
        
        r = requests.put(get_file_url(), headers=get_headers(), json=payload, timeout=10)
        return r.status_code in [200, 201]
    except Exception as e:
        st.sidebar.error(f"❌ {e}")
        return False

# ИНИЦИАЛИЗАЦИЯ
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

# ДАННЫЕ
EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']
DAYS_IN_MONTH = {'ИЮЛЬ': 31, 'АВГУСТ': 31, 'СЕНТЯБРЬ': 30, 'ОКТЯБРЬ': 31, 'НОЯБРЬ': 30, 'ДЕКАБРЬ': 31}

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
        'locked': st.session_state.locked_data
    }

# ИНТЕРФЕЙС
st.sidebar.title("📊 Учёт часов")

if st.sidebar.button(" СОХРАНИТЬ В GITHUB", type="primary", use_container_width=True):
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
            st.session_state.locked_data = data.get('locked', {})
            st.sidebar.success("✅ Загружено!")
            st.rerun()
        else:
            st.sidebar.error("❌ Ошибка загрузки!")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "dashboard", "activity", "votes", "rating"])
month = st.sidebar.selectbox("📅 Месяц", MONTHS)

# ВВОД ЧАСОВ
if page == "input":
    st.title(f"⏱️ Ввод часов - {month}")
    days_count = DAYS_IN_MONTH[month]
    
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
        column_config[str(day)] = st.column_config.NumberColumn(str(day), min_value=0.0, max_value=24.0, step=0.5, format='%.1f', width='small')
    
    edited_df = st.data_editor(df_input, column_config=column_config, hide_index=True, use_container_width=True, num_rows='fixed', key='hours_table')
    
    st.markdown("---")
    
    if st.button("💾 СОХРАНИТЬ ДАННЫЕ", type="primary", use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                new_hours = []
                for day in range(1, days_count + 1):
                    try: val = float(edited_df.iloc[idx][str(day)])
                    except: val = 0.0
                    new_hours.append(val)
                while len(new_hours) < 31: new_hours.append(0.0)
                st.session_state.hours_data[f"{month}_{emp}"] = new_hours[:31]
                total = sum(new_hours[:31])
                if total > 0:
                    st.session_state.feed.insert(0, {
                        'time': datetime.now().strftime('%d.%m %H:%M'),
                        'emoji': '⏱',
                        'message': f'{emp}: {total:.1f} ч'
                    })
        
        ok = save_to_github(get_all_data())
        if ok:
            st.success("✅ ДАННЫЕ СОХРАНЕНЫ В GITHUB!")
            st.balloons()
        else:
            st.error("❌ ОШИБКА СОХРАНЕНИЯ!")
        st.rerun()

# ДАШБОРД
elif page == "dashboard":
    st.title(f"📊 Дашборд - {month}")
    stats = [{'Сотрудник': emp, 'Часы': sum(get_hours(month, emp))} for emp in EMPLOYEES]
    df = pd.DataFrame(stats)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if df['Часы'].sum() > 0:
        st.bar_chart(df.set_index('Сотрудник'))

# ЛЕНТА
elif page == "activity":
    st.title("📱 Лента активности")
    if len(st.session_state.feed) == 0:
        st.info("📭 Лента пуста.")
    else:
        for item in st.session_state.feed:
            st.markdown(f"**{item['time']}** {item['emoji']} {item['message']}")
    if st.button("🗑️ Очистить"):
        st.session_state.feed = []
        save_to_github(get_all_data())
        st.rerun()

# ГОЛОСОВАНИЯ
elif page == "votes":
    st.title("🗳️ Голосования")
    voter = st.selectbox(" Кто голосует?", ['— Выбери себя —'] + EMPLOYEES)
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

# РЕЙТИНГ
elif page == "rating":
    st.title(f"🏆 Рейтинг - {month}")
    stats = [{'Сотрудник': emp, 'Часы': sum(get_hours(month, emp))} for emp in EMPLOYEES]
    df = pd.DataFrame(stats).sort_values('Часы', ascending=False)
    st.dataframe(df, use_container_width=True)
