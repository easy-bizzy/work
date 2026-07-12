import streamlit as st
import pandas as pd
from datetime import date

# ============================================
# НАСТРОЙКИ + СВЕТЛАЯ ТЕМА
# ============================================
st.set_page_config(
    page_title="Учёт времени",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    h1, h2, h3, h4, h5, h6 { color: #000000 !important; }
    
    [data-testid="stSidebar"] {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span { color: #FFFFFF !important; }
    
    .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #333333 !important;
    }
    
    .stButton > button {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #333333 !important; }
    
    .stSuccess { background-color: #d4edda !important; color: #155724 !important; }
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

CALENDAR = {
    'ИЮЛЬ': {'weekends': [4,5,11,12,18,19,25,26], 'holidays': [], 'short': []},
    'АВГУСТ': {'weekends': [1,2,8,9,15,16,22,23,29,30], 'holidays': [], 'short': []},
    'СЕНТЯБРЬ': {'weekends': [5,6,12,13,19,20,26,27], 'holidays': [], 'short': []},
    'ОКТЯБРЬ': {'weekends': [3,4,10,11,17,18,24,25,31], 'holidays': [], 'short': []},
    'НОЯБРЬ': {'weekends': [1,7,8,14,15,21,22,28,29], 'holidays': [4], 'short': [3]},
    'ДЕКАБРЬ': {'weekends': [5,6,12,13,19,20,26,27], 'holidays': [], 'short': [31]},
}

MONTH_NUM = {'ИЮЛЬ': 7, 'АВГУСТ': 8, 'СЕНТЯБРЬ': 9, 'ОКТЯБРЬ': 10, 'НОЯБРЬ': 11, 'ДЕКАБРЬ': 12}
DAYS_IN_MONTH = {'ИЮЛЬ': 31, 'АВГУСТ': 31, 'СЕНТЯБРЬ': 30, 'ОКТЯБРЬ': 31, 'НОЯБРЬ': 30, 'ДЕКАБРЬ': 31}
WEEKDAYS_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

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
page = st.sidebar.radio(' Меню', ['📊 Дашборд', '✏️ Ввод часов', ' Рейтинг'])
month = st.sidebar.selectbox(' Месяц', MONTHS)
norm = MONTHS_DATA[month]

# ============================================
# СТРАНИЦА 1: ДАШБОРД
# ============================================
if page == ' Дашборд':
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
    with col1: st.metric('⏱ Всего часов', f"{df['Часы'].sum():.1f}")
    with col2: st.metric('🔥 Переработка', f"{df['Переработка'].sum():.1f} ч")
    with col3: st.metric('📈 Ср. эффективность', f"{df['Эффективность %'].mean():.0f}%")
    
    st.markdown('---')
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('⏱ Часы по сотрудникам')
        st.bar_chart(df.set_index('Сотрудник')['Часы'])
    with col2:
        st.subheader('🔥 Переработка')
        st.bar_chart(df.set_index('Сотрудник')['Переработка'])
    
    st.markdown('---')
    st.subheader(' Сводная таблица')
    st.dataframe(df, use_container_width=True)

# ============================================
# СТРАНИЦА 2: ВВОД ЧАСОВ (С АВТОСОХРАНЕНИЕМ)
# ============================================
elif page == '✏️ Ввод часов':
    st.title(f'✏️ Ввод часов — {month}')
    
    cal = CALENDAR[month]
    year = 2026
    month_num = MONTH_NUM[month]
    days_count = DAYS_IN_MONTH[month]
    
    emp = st.selectbox('👤 Сотрудник', EMPLOYEES)
    hours = get_hours(month, emp)
    
    st.markdown(f'###  Часы для: **{emp}** в **{month} 2026**')
    
    workdays_count = sum(1 for d in range(1, days_count+1) 
                        if d not in cal['weekends'] and d not in cal['holidays'])
    st.markdown(f'**Норма месяца:** {norm} ч | **Рабочих дней:** {workdays_count}')
    
    # Создаём таблицу
    table_data = []
    for day in range(1, days_count + 1):
        dt = date(year, month_num, day)
        weekday = WEEKDAYS_RU[dt.weekday()]
        
        if day in cal['holidays']:
            day_type = '🔴 Праздник'
        elif day in cal['short']:
            day_type = ' Сокращённый'
        elif day in cal['weekends']:
            day_type = ' Выходной'
        else:
            day_type = 'Рабочий'
        
        h = float(hours[day-1]) if day-1 < len(hours) else 0.0
        overtime = max(0, h - 8) if h > 0 else 0
        
        table_data.append({
            'День': day,
            'Дата': dt.strftime('%d.%m.%Y'),
            'День недели': weekday,
            'Тип дня': day_type,
            'Часы': h,
            'Переработка': overtime
        })
    
    df_input = pd.DataFrame(table_data)
    
    # Редактируемая таблица
    edited_df = st.data_editor(
        df_input,
        column_config={
            'День': st.column_config.NumberColumn('День', width='small', disabled=True),
            'Дата': st.column_config.TextColumn('Дата', width='medium', disabled=True),
            'День недели': st.column_config.TextColumn('День', width='small', disabled=True),
            'Тип дня': st.column_config.TextColumn('Тип дня', width='medium', disabled=True),
            'Часы': st.column_config.NumberColumn(
                'Часы',
                min_value=0.0,
                max_value=24.0,
                step=0.5,
                format='%.1f',
                width='small'
            ),
            'Переработка': st.column_config.NumberColumn(
                'Переработка',
                format='%.1f',
                width='small',
                disabled=True,
                help='Считается автоматически'
            ),
        },
        hide_index=True,
        use_container_width=True,
        num_rows='fixed',
        key=f'editor_{month}_{emp}'
    )
    
    #  АВТОСОХРАНЕНИЕ: при любом изменении сохраняем сразу
    new_hours = edited_df['Часы'].tolist()
    while len(new_hours) < 31:
        new_hours.append(0.0)
    new_hours = new_hours[:31]
    
    # Пересчитываем переработку
    edited_df['Переработка'] = edited_df['Часы'].apply(
        lambda x: round(max(0, x - 8), 1) if x > 0 else 0.0
    )
    
    # Сохраняем автоматически
    save_hours(month, emp, new_hours)
    
    # Показываем статус автосохранения
    st.success('💾 Автосохранено', icon='💾')
    
    # ИТОГО
    total_hours = edited_df['Часы'].sum()
    total_overtime = edited_df['Переработка'].sum()
    workdays_worked = int((edited_df['Часы'] > 0).sum())
    efficiency = (total_hours / norm * 100) if norm > 0 else 0
    
    st.markdown('---')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric('⏱ ��ТОГО часов', f'{total_hours:.1f}')
    with col2: st.metric('🔥 Переработка', f'{total_overtime:.1f} ч')
    with col3: st.metric('📈 Эффективность', f'{efficiency:.0f}%')
    with col4: st.metric('📅 Рабочих дней', workdays_worked)
    
    # Легенда
    st.markdown('---')
    st.markdown('**📌 Легенда:**')
    st.markdown('🔴 **Праздник** | 🟠 **Сокращённый** |  **Выходной** | **Рабочий** — обычный день')
    st.markdown('💡 **Переработка** = часы − 8 (если больше 8). Считается автоматически.')

# ============================================
# СТРАНИЦА 3: РЕЙТИНГ
# ============================================
elif page == ' Рейтинг':
    st.title(f' Рейтинг — {month}')
    
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
    st
