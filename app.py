import streamlit as st
import pandas as pd
from datetime import date

# ============================================
# НАСТРОЙКИ СТРАНИЦЫ (тёмная тема по умолчанию)
# ============================================
st.set_page_config(
    page_title="Учёт времени | ОАЗИС",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ДАННЫЕ И КАЛЕНДАРЬ
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
    overtime = sum(max(0, h - 8) for h in hours if h > 0)
    efficiency = (total / norm * 100) if norm > 0 else 0
    return total, overtime, efficiency

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title('🏆 ОАЗИС')
page = st.sidebar.radio('📋 Меню', [' Дашборд', '✏️ Ввод часов', '🏆 Рейтинг'])
month = st.sidebar.selectbox('📅 Месяц', MONTHS)
norm = MONTHS_DATA[month]

# ============================================
# СТРАНИЦА 1: ДАШБОРД (ИСПРАВЛЕН)
# ============================================
if page == '📊 Дашборд':
    st.title(f'📊 Дашборд — {month} 2026')
    
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
    
    # KPI
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('⏱ Всего часов', f"{df['Часы'].sum():.1f}")
    with col2:
        st.metric('🔥 Переработка', f"{df['Переработка'].sum():.1f} ч")
    with col3:
        st.metric('📈 Ср. эффективность', f"{df['Эффективность %'].mean():.0f}%")
    
    st.markdown('---')
    
    # Графики
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
# СТРАНИЦА 2: ВВОД ЧАСОВ (КАК В EXCEL)
# ============================================
elif page == '✏️ Ввод часов':
    st.title(f'✏️ Ввод часов — {month} 2026')
    st.info('💡 Кликай на ячейку и вводи часы. Нажми "Сохранить" когда закончишь.')
    
    cal = CALENDAR[month]
    year = 2026
    month_num = MONTH_NUM[month]
    days_count = DAYS_IN_MONTH[month]
    
    # Формируем таблицу: строки = сотрудники, колонки = дни + ИТОГО + ПЕРЕРАБ
    table_data = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        row = {'Сотрудник': emp}
        
        for day in range(1, days_count + 1):
            h = float(hours[day-1]) if day-1 < len(hours) else 0.0
            row[str(day)] = h
        
        # ИТОГО и ПЕРЕРАБ считаем сразу
        total = sum(row[str(day)] for day in range(1, days_count + 1))
        overtime = sum(max(0, row[str(day)] - 8) for day in range(1, days_count + 1) if row[str(day)] > 0)
        row['ИТОГО'] = round(total, 1)
        row['ПЕРЕРАБ'] = round(overtime, 1)
        
        table_data.append(row)
    
    df_input = pd.DataFrame(table_data)
    
    # Настройка колонок
    column_config = {
        'Сотрудник': st.column_config.TextColumn('Сотрудник', width='medium', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', width='small', disabled=True),
        'ПЕРЕРАБ': st.column_config.NumberColumn('ПЕРЕРАБ', format='%.1f', width='small', disabled=True),
    }
    
    for day in range(1, days_count + 1):
        column_config[str(day)] = st.column_config.NumberColumn(
            str(day),
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            format='%.1f',
            width='small'
        )
    
    # Редактируемая таблица
    edited_df = st.data_editor(
        df_input,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows='fixed',
        key='hours_table'
    )
    
    # Пересчёт ИТОГО и ПЕРЕРАБ после редактирования
    for idx in range(len(edited_df)):
        total = sum(float(edited_df.iloc[idx][str(day)]) for day in range(1, days_count + 1))
        overtime = sum(max(0, float(edited_df.iloc[idx][str(day)]) - 8) 
                      for day in range(1, days_count + 1) 
                      if float(edited_df.iloc[idx][str(day)]) > 0)
        edited_df.at[edited_df.index[idx], 'ИТОГО'] = round(total, 1)
        edited_df.at[edited_df.index[idx], 'ПЕРЕРАБ'] = round(overtime, 1)
    
    # Кнопка сохранения
    st.markdown('---')
    if st.button(' СОХРАНИТЬ ВСЕ ДАННЫЕ', type='primary', use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                new_hours = [float(edited_df.iloc[idx][str(day)]) for day in range(1, days_count + 1)]
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                save_hours(month, emp, new_hours[:31])
        st.success('✅ Все данные сохранены!')
    
    # Итоги по команде
    st.markdown('---')
    st.subheader('📊 Итоги по команде')
    
    total_hours_all = sum(float(edited_df.iloc[idx]['ИТОГО']) for idx in range(len(edited_df)))
    total_overtime_all = sum(float(edited_df.iloc[idx]['ПЕРЕРАБ']) for idx in range(len(edited_df)))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('⏱ Всего часов по команде', f'{total_hours_all:.1f}')
    with col2:
        st.metric('🔥 Всего переработок', f'{total_overtime_all:.1f} ч')
    with col3:
        avg_eff = sum(calc_stats(get_hours(month, emp), norm)[2] for emp in EMPLOYEES) / len(EMPLOYEES)
        st.metric('📈 Средняя эффективность', f'{avg_eff:.0f}%')
    
    # Легенда
    st.markdown('---')
    st.markdown('**📌 Легенда:** 🔴 Праздник | 🟠 Сокращённый | ⚪ Выходной')
    st.markdown('💡 **Переработка** = всё что больше 8 часов в день')

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
            <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;">
            <h2>🥈</h2>
            <h3>{df.iloc[1]["Сотрудник"]}</h3>
            <p><b>{df.iloc[1]["Часы"]:.1f} ч</b></p>
            <p>Переработка: {df.iloc[1]["Переработка"]:.1f} ч</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:30px; border-radius:10px; text-align:center; border:3px solid gold;">
            <h1>🥇</h1>
            <h2>{df.iloc[0]["Сотрудник"]}</h2>
            <p style="font-size:24px;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p>
            <p>Переработка: {df.iloc[0]["Переработка"]:.1f} ч</p>
            <p style="font-size:20px; color:#000;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'''
            <div style="background:#CD7F32; padding:20px; border-radius:10px; text-align:center;">
            <h2>🥉</h2>
            <h3>{df.iloc[2]["Сотрудник"]}</h3>
            <p><b>{df.iloc[2]["Часы"]:.1f} ч</b></p>
            <p>Переработка: {df.iloc[2]["Переработка"]:.1f} ч</p>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('---')
    st.subheader(' Полный рейтинг')
    st.dataframe(df, use_container_width=True)
    
    st.markdown('---')
    st.subheader('🏅 Награды месяца')
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:20px; border-radius:10px; border:2px solid gold;">
        <h2>🏆 ГРАМОТА</h2>
        <h3 style="color:#000;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3>
        <p><b>{df.iloc[0]["Сотрудник"]}</b></p>
        <p>{df.iloc[0]["Часы"]:.1f} часов | {df.iloc[0]["Переработка"]:.1f} ч переработки</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div style="background:linear-gradient(135deg, #8B4513, #654321); padding:20px; border-radius:10px; border:2px solid #8B4513;">
        <h2>📜 АНТИНАГРАДА</h2>
        <h3 style="color:#FFD700;">ЛОХ</h3>
        <p><b>{df.iloc[-1]["Сотрудник"]}</b></p>
        <p>{df.iloc[-1]["Часы"]:.1f} часов | эффективность {df.iloc[-1]["Эффективность %"]:.0f}%</p>
        </div>
        ''', unsafe_allow_html=True)
