import streamlit as st
import pandas as pd

# ============================================
# НАСТРОЙКИ + СВЕТЛАЯ ТЕМА
# ============================================
st.set_page_config(
    page_title="Учёт времени",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS для контраста
st.markdown("""
<style>
    /* Светлая тема для всего приложения */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    
    /* Заголовки - чёрные на белом */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }
    
    /* Боковая панель - чёрный фон, белый текст */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: #FFFFFF !important;
    }
    
    /* Поля ввода - явные границы */
    .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #333333 !important;
    }
    
    /* Кнопки */
    .stButton > button {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    .stButton > button:hover {
        background-color: #45a049 !important;
    }
    
    /* Метрики - контрастные */
    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #333333 !important;
    }
    
    /* Таблицы */
    .dataframe {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Успешные сообщения */
    .stSuccess {
        background-color: #d4edda !important;
        color: #155724 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ДАННЫЕ
# ============================================
EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']
MONTHS_DATA = {
    'ИЮЛЬ': 184, 'АВГУСТ': 168, 'СЕНТЯБРЬ': 176,
    'ОКТЯБРЬ': 176, 'НОЯБРЬ': 160, 'ДЕКАБРЬ': 184
}

# ============================================
# ХРАНЕНИЕ ДАННЫХ
# ============================================
@st.cache_resource
def get_data():
    return {'hours': {}}

data = get_data()

def get_hours(month, emp):
    key = f"{month}_{emp}"
    return data['hours'].get(key, [0.0] * 31)

def save_hours(month, emp, hours):
    key = f"{month}_{emp}"
    data['hours'][key] = hours

def calc_stats(hours, norm):
    total = sum(hours)
    overtime = sum(max(0, h - 8) for h in hours)
    efficiency = (total / norm * 100) if norm > 0 else 0
    return total, overtime, efficiency

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title('🏆 ОАЗИС')
page = st.sidebar.radio('📋 Меню', ['📊 Дашборд', '✏️ Ввод часов', '🏆 Рейтинг'])
month = st.sidebar.selectbox('📅 Месяц', MONTHS)
norm = MONTHS_DATA[month]

# ============================================
# СТРАНИЦА 1: ДАШБОРД
# ============================================
if page == '📊 Дашборд':
    st.title(f'📊 Дашборд — {month}')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency = calc_stats(hours, norm)
        stats_list.append({
            'Сотрудник': emp,
            'Часы': total,
            'Переработка': overtime,
            'Эффективность %': round(efficiency, 1)
        })
    
    df = pd.DataFrame(stats_list)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('⏱ Всего часов', f"{df['Часы'].sum():.1f}")
    with col2:
        st.metric('🔥 Переработка', f"{df['Переработка'].sum():.1f} ч")
    with col3:
        st.metric('📈 Ср. эффективность', f"{df['Эффективность %'].mean():.0f}%")
    
    st.markdown('---')
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('⏱ Часы по сотрудникам')
        st.bar_chart(df.set_index('Сотрудник')['Часы'])
    with col2:
        st.subheader('🔥 Переработка')
        st.bar_chart(df.set_index('Сотрудник')['Переработка'])
    
    st.markdown('---')
    st.subheader('📋 Сводная таблица')
    st.dataframe(df, use_container_width=True)

# ============================================
# СТРАНИЦА 2: ВВОД ЧАСОВ (ИСПРАВЛЕННАЯ)
# ============================================
elif page == '✏️ Ввод часов':
    st.title(f'✏️ Ввод часов — {month}')
    
    st.info('💡 Введи часы за каждый день. Если не работал — оставь 0. Дробные числа через точку (например, 8.5)')
    
    emp = st.selectbox('👤 Сотрудник', EMPLOYEES)
    
    hours = get_hours(month, emp)
    
    st.markdown(f'### 📝 Часы для: **{emp}**')
    st.markdown('**Норма: 8 часов в день. Всё что больше — идёт в переработку.**')
    
    # Ввод по неделям для удобства
    new_hours = []
    for week in range(5):
        st.markdown(f'#### 📅 Неделя {week + 1}')
        cols = st.columns(7)
        for i in range(7):
            day = week * 7 + i + 1
            if day > 31:
                break
            val = cols[i].number_input(
                f'День {day}',
                min_value=0.0,
                max_value=24.0,
                value=float(hours[day-1]),
                step=0.5,
                key=f'd{day}_{emp}'
            )
            new_hours.append(val)
    
    # Дополняем до 31 дня
    while len(new_hours) < 31:
        new_hours.append(0.0)
    
    st.markdown('---')
    
    if st.button('💾 СОХРАНИТЬ', type='primary', use_container_width=True):
        save_hours(month, emp, new_hours)
        st.success('✅ Данные сохранены!')
        st.balloons()
    
    # Статистика
    total, overtime, efficiency = calc_stats(new_hours, norm)
    
    st.markdown('---')
    st.subheader('📊 Твоя статистика')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('⏱ Всего часов', f'{total:.1f}')
    with col2:
        st.metric('🔥 Переработка', f'{overtime:.1f} ч')
    with col3:
        st.metric('📈 Эффективность', f'{efficiency:.0f}%')
    with col4:
        workdays = sum(1 for h in new_hours if h > 0)
        st.metric('📅 Рабочих дней', workdays)

# ============================================
# СТРАНИЦА 3: РЕЙТИНГ
# ============================================
elif page == '🏆 Рейтинг':
    st.title(f'🏆 Рейтинг — {month}')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency = calc_stats(hours, norm)
        stats_list.append({
            'Сотрудник': emp,
            'Часы': total,
            'Переработка': overtime,
            'Эффективность %': round(efficiency, 1)
        })
    
    df = pd.DataFrame(stats_list).sort_values('Часы', ascending=False).reset_index(drop=True)
    
    st.markdown('---')
    st.subheader('🏆 Подиум')
    
    if len(df) >= 3:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f'''
            <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center; color:black;">
            <h2>🥈</h2>
            <h3 style="color:black;">{df.iloc[1]["Сотрудник"]}</h3>
            <p style="color:black;"><b>{df.iloc[1]["Часы"]:.1f} ч</b></p>
            <p style="color:black;">Переработка: {df.iloc[1]["Переработка"]:.1f} ч</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div style="background:#FFD700; padding:30px; border-radius:10px; text-align:center; border:3px solid gold; color:black;">
            <h1>🥇</h1>
            <h2 style="color:black;">{df.iloc[0]["Сотрудник"]}</h2>
            <p style="font-size:24px; color:black;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p>
            <p style="color:black;">Переработка: {df.iloc[0]["Переработка"]:.1f} ч</p>
            <p style="color:darkblue; font-size:18px;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'''
            <div style="background:#CD7F32; padding:20px; border-radius:10px; text-align:center; color:white;">
            <h2>🥉</h2>
            <h3 style="color:white;">{df.iloc[2]["Сотрудник"]}</h3>
            <p style="color:white;"><b>{df.iloc[2]["Часы"]:.1f} ч</b></p>
            <p style="color:white;">Переработка: {df.iloc[2]["Переработка"]:.1f} ч</p>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('---')
    st.subheader('📋 Полный рейтинг')
    st.dataframe(df, use_container_width=True)
    
    st.markdown('---')
    st.subheader('🏅 Награды месяца')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div style="background:#FFD700; padding:20px; border-radius:10px; color:black; border:2px solid gold;">
        <h2 style="color:black;">🏆 ГРАМОТА</h2>
        <h3 style="color:darkblue;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3>
        <p style="color:black;"><b>{df.iloc[0]["Сотрудник"]}</b></p>
        <p style="color:black;">{df.iloc[0]["Часы"]:.1f} часов</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div style="background:#8B4513; padding:20px; border-radius:10px; color:white; border:2px solid #8B4513;">
        <h2 style="color:white;">📜 АНТИНАГРАДА</h2>
        <h3 style="color:#FFD700;">ЛОХ</h3>
        <p style="color:white;"><b>{df.iloc[-1]["Сотрудник"]}</b></p>
        <p style="color:white;">{df.iloc[-1]["Часы"]:.1f} часов</p>
        </div>
        ''', unsafe_allow_html=True)
