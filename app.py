import streamlit as st
import pandas as pd
import json
from datetime import datetime
import requests

st.set_page_config(page_title="Учёт часов", page_icon="📊", layout="wide")

# ============================================
# НАСТРОЙКИ
# ============================================
API_KEY = "<LaTex>id_1</LaTex>10$fdP3BAMcCh8G0kJpVurg7.fqWCvq9jsXK.yzOcd0ynCzs4H2PEoVC"
BIN_ID = "6a550654da38895dfe578dd3"

EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']

# ============================================
# ФУНКЦИИ ОБЛАКА С ДИАГНОСТИКОЙ
# ============================================
def load_from_cloud():
    """Загрузка с полной диагностикой"""
    headers = {'X-Master-Key': API_KEY}
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}/latest'
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Показываем что получили
        st.sidebar.write(f"**GET ответ:** {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            record = data.get('record', {})
            hours = record.get('hours', {})
            st.sidebar.write(f"**Записей в облаке:** {len(hours)}")
            if hours:
                st.sidebar.write(f"**Пример:** {list(hours.keys())[:3]}")
            return record, True
        else:
            st.sidebar.error(f"Ошибка загрузки: {response.status_code}")
            st.sidebar.code(response.text[:200])
            return None, False
    except Exception as e:
        st.sidebar.error(f"Исключение: {e}")
        return None, False

def save_to_cloud(data):
    """Сохранение с полной диагностикой"""
    headers = {'X-Master-Key': API_KEY, 'Content-Type': 'application/json'}
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    
    try:
        # Показываем что отправляем
        hours_count = len(data.get('hours', {}))
        st.sidebar.write(f"**Отправляем записей:** {hours_count}")
        if data.get('hours'):
            st.sidebar.write(f"**Пример ключей:** {list(data['hours'].keys())[:3]}")
        
        response = requests.put(url, headers=headers, json=data, timeout=10)
        
        st.sidebar.write(f"**PUT ответ:** {response.status_code}")
        
        if response.status_code == 200:
            st.sidebar.success("✅ Сохранено успешно!")
            return True
        else:
            st.sidebar.error(f"Ошибка сохранения: {response.status_code}")
            st.sidebar.code(response.text[:300])
            return False
    except Exception as e:
        st.sidebar.error(f"Исключение: {e}")
        return False

# ============================================
# ЗАГРУЗКА ДАННЫХ ПРИ СТАРТЕ (ВСЕГДА)
# ============================================
st.sidebar.markdown("### 🔄 Загрузка при старте")
cloud_data, load_ok = load_from_cloud()

if load_ok and cloud_data:
    st.session_state.hours_data = cloud_data.get('hours', {})
    st.session_state.feed = cloud_data.get('feed', [])
    st.session_state.votes = cloud_data.get('votes', {'hardworker': {}, 'slacker
