import streamlit as st
import pandas as pd
import requests
import base64
import json
from datetime import datetime

st.set_page_config(page_title="Учёт часов", page_icon="", layout="wide")

# НАСТРОЙКИ
GITHUB_TOKEN = "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"
REPO_OWNER = "easy-bizzy"
REPO_NAME = "work"
FILE_PATH = "data.json"

def get_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def get_file_url():
    return f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

def load_from_github():
    """Загрузка с полной диагностикой"""
    url = get_file_url()
    st.sidebar.write(f"**URL:** `{url}`")
    
    try:
        r = requests.get(url, headers=get_headers(), timeout=10)
        st.sidebar.write(f"**GET статус:** {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            st.sidebar.write(f"**SHA:** {data.get('sha', 'N/A')[:20]}...")
            
            content = base64.b64decode(data['content']).decode('utf-8')
            st.sidebar.write(f"**Размер:** {len(content)} байт")
            
            parsed = json.loads(content)
            st.sidebar.success(f"✅ Загружено!")
            return parsed, True
        elif r.status_code == 404:
            st.sidebar.error("❌ Файл data.json не найден! Создай его в репозитории.")
            return None, False
        elif r.status_code == 401:
            st.sidebar.error("❌ Неверный токен!")
            return None, False
        elif r.status_code == 403:
            st.sidebar.error("❌ Нет прав доступа. Проверь токен.")
            return None, False
        else:
            st.sidebar.error(f"❌ Ошибка {r.status_code}: {r.text[:100]}")
            return None, False
    except Exception as e:
        st.sidebar.error(f"❌ Исключение: {e}")
        return None, False

def save_to_github(data):
    """Сохранение с полной диагностикой"""
    url = get_file_url()
    
    try:
        # Сначала получаем текущий файл
        r = requests.get(url, headers=get_headers(), timeout=10)
        st.sidebar.write(f"**GET для SHA:** {r.status_code}")
        
        if r.status_code == 200:
            sha = r.json()['sha']
            st.sidebar.write(f"**SHA:** {sha[:20]}...")
        elif r.status_code == 404:
            st.sidebar.warning("⚠️ Файл не существует, создаём новый")
            sha = None
        else:
            st.sidebar.error(f"❌ Ошибка получения SHA: {r.status_code}")
            return False
        
        # Кодируем данные
        content = json.dumps(data, ensure_ascii=False, indent=2)
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        st.sidebar.write(f"**Размер данных:** {len(content)} байт")
        
        # Формируем payload
        payload = {
            "message": f"Update {datetime.now().strftime('%H:%M:%S')}",
            "content": encoded,
            "branch": "main"
        }
        
        if sha:
            payload["sha"] = sha
        
        # Отправляем
        r = requests.put(url, headers=get_headers(), json=payload, timeout=10)
        st.sidebar.write(f"**PUT статус:** {r.status_code}")
        
        if r.status_code in [200, 201]:
            st.sidebar.success("✅ Сохранено!")
            return True
        else:
            st.sidebar.error(f"❌ Ошибка сохранения: {r.status_code}")
            st.sidebar.code(r.text[:200])
            return False
    except Exception as e:
        st.sidebar.error(f"❌ Исключение: {e}")
        return False

# ИНИЦИАЛИЗАЦИЯ
st.sidebar.markdown("### 🔍 Диагностика")
data, ok = load_from_github()

if ok and data:
    st.session_state.hours_data = data.get('hours', {})
    st.session_state.feed = data.get('feed', [])
    st.session_state.votes = data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
    st.session_state.locked_data = data.get('locked', {})
    st.sidebar.success(f"✅ Загружено {len(st.session_state.hours_data)} записей")
else:
    st.session_state.hours_data = {}
    st.session_state.feed = []
    st.session_state.votes = {'hardworker': {}, 'slacker': {}, 'voters': []}
    st.session_state.locked_data = {}
    st.sidebar.warning("⚠️ Начинаем с нуля")

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
st.sidebar.markdown("---")
st.sidebar.write(f"Записей в памяти: {len(st.session_state.hours_data)}")

if st.sidebar.button("💾 СОХРАНИТЬ", type="primary", use_container_width=True):
    with st.spinner("Сохранение..."):
        ok = save_to_github(get_all_data())
        if ok:
            st.success("✅ Сохранено в GitHub!")
        else:
            st.error("❌ Ошибка! Смотри диагностику в боковой панели.")

st.sidebar.markdown("---")
page = st.sidebar.radio("Меню", ["input", "dashboard"])
month = st.sidebar.selectbox("Месяц", MONTHS)

# ВВОД ЧАСОВ
if page == "input":
    st.title(f"Ввод часов - {month}")
    
    days_count = DAYS_IN_MONTH[month]
    
    st.markdown("### Текущие данные:")
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total = sum(hours)
        if total > 0:
            st.write(f"- {emp}: {total:.1f} ч")
    
    st.markdown("---")
    
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
        st.write("### Сохранение...")
        
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
                st.write(f"✅ {emp}: {total:.1f} ч")
        
        st.write(f"**Всего записей: {len(st.session_state.hours_data)}**")
        
        ok = save_to_github(get_all_data())
        if ok:
            st.success("✅ ДАННЫЕ СОХРАНЕНЫ!")
            st.balloons()
        else:
            st.error("❌ ОШИБКА! Смотри боковую панель.")
        
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
    else:
        st.info("Нет данных.")
