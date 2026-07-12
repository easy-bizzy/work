import streamlit as st
import pandas as pd
import json
from datetime import date

st.set_page_config(
    page_title="Учёт рабочего времени",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

MONTH_NUM = {'ИЮЛЬ': 7, 'АВГУСТ': 8, 'СЕНТЯБРЬ': 9, 'ОКТЯБРЬ': 10, 'НОЯБРЬ': 11, 'ДЕКАБРЬ': 12}
DAYS_IN_MONTH = {'ИЮЛЬ': 31, 'АВГУСТ': 31, 'СЕНТЯБРЬ': 30, 'ОКТЯБРЬ': 31, 'НОЯБРЬ': 30, 'ДЕКАБРЬ': 31}

if 'hours_data' not in st.session_state:
    st.session_state.hours_data = {}

def get_hours(month, emp):
    key = f"{month}_{emp}"
    return st.session_state.hours_data.get(key, [0.0] * 31)

def save_hours(month, emp, hours):
    key = f"{month}_{emp}"
    st.session_state.hours_data[key] = hours

def calc_stats(hours, norm, workdays):
    total = sum(hours)
    overtime = sum(max(0, h - 8) for h in hours if h > 0)
    efficiency = (total / norm * 100) if norm > 0 else 0
    remaining_hours = max(0, norm - total)
    workdays_worked = sum(1 for h in hours if h > 0)
    remaining_days = max(0, workdays - workdays_worked)
    return total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days

# ============================================
# БОКОВАЯ ПАНЕЛЬ (БЕЗ ЭМОДЗИ В НАЗВАНИЯХ ДЛЯ СРАВНЕНИЯ)
# ============================================
st.sidebar.title('📊 Учет рабочего времени')

st.sidebar.markdown('### 💾 Управление данными')
data_json = json.dumps(st.session_state.hours_data, ensure_ascii=False)
st.sidebar.download_button(
    label='📥 Скачать бэкап',
    data=data_json,
    file_name=f'backup_{date.today().strftime("%Y%m%d")}.json',
    mime='application/json',
    use_container_width=True
)

uploaded_file = st.sidebar.file_uploader('📤 Загрузить бэкап', type=['json'])
if uploaded_file is not None:
    try:
        new_data = json.load(uploaded_file)
        st.session_state.hours_data = new_data
        st.sidebar.success('✅ Данные загружены!')
    except Exception as e:
        st.sidebar.error(f'❌ Ошибка: {e}')

st.sidebar.markdown('---')

# Простые названия без эмодзи для надёжного сравнения
page = st.sidebar.radio('Меню', ['dashboard', 'input', 'rating'])
month = st.sidebar.selectbox(' Месяц', MONTHS)

month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

st.sidebar.markdown('---')
st.sidebar.markdown(f'**📅 {month} 2026**')
st.sidebar.markdown(f'Рабочих дней: **{workdays}**')
st.sidebar.markdown(f'Норма часов: **{norm}**')

# ============================================
# ДАШБОРД
# ============================================
if page == 'dashboard':
    st.title(f'📊 Дашборд — {month} 2026')
    
    # СТАРЫЙ ДАШБОРД (как был)
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days = calc_stats(hours, norm, workdays)
        stats_list.append({
            'Сотрудник': emp,
            'Отработано часов': total,
            'Норма часов': norm,
            'Осталось часов': remaining_hours,
            'Процент выполнения': f'{efficiency:.1f}%',
            'Отработано дней': workdays_worked,
            'Рабочих дней в месяце': workdays,
            'Осталось дней': remaining_days,
            'Переработка': overtime
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
    st.subheader('🏆 Статистика')
    col1, col2, col3 = st.columns(3)
    with col1:
        top_worker = df.loc[df['Отработано часов'].idxmax()]
        st.metric('🏆 Лидер месяца', top_worker['Сотрудник'], f"{top_worker['Отработано часов']:.1f} ч")
    with col2:
        st.metric('🔥 Всего переработок', f"{df['Переработка'].sum():.1f} ч")
    with col3:
        completed = len(df[df['Осталось часов'] == 0])
        st.metric('✅ Выполнили норму', f'{completed} чел.')
    
    # НОВАЯ СЕКЦИЯ: КАРТОЧКИ СОТРУДНИКОВ (ниже)
    st.markdown('---')
    st.subheader(' Детальная статистика по сотрудникам')
    st.markdown('**Прокрути вниз чтобы увидеть информацию по каждому сотруднику**')
    
    # Сортируем по часам
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
            st.metric('⏱ Всего часов', f"{row['Отработано часов']:.1f} / {norm}")
        with col2:
            st.metric(' Рабочих дней', f"{row['Отработано дней']} / {workdays}")
        with col3:
            st.metric('🔥 Переработка', f"{row['Переработка']:.1f} ч")
        with col4:
            remaining = row['Осталось часов']
            if remaining > 0:
                st.metric('⏳ Осталось часов', f"{remaining:.1f} ч")
            else:
                st.metric('✅ Норма выполнена', f"+{row['Отработано часов'] - norm:.1f} ч")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**📊 % выполнения по часам:** {row['Процент выполнения']}")
        with col2:
            days_percent = (row['Отработано дней'] / workdays * 100) if workdays > 0 else 0
            st.markdown(f"**📅 % выполнения по дням:** {days_percent:.1f}%")
        
        # Бесцветный прогресс-бар
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
# ВВОД ЧАСОВ
# ============================================
elif page == 'input':
    st.title(f'✏️ Ввод часов — {month} 2026')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info(f'📅 Рабочих дней: **{workdays}**')
    with col2: st.info(f'⏱ Норма часов: **{norm}**')
    with col3: st.info(f'🔴 Праздников: **{len(month_info["holidays"])}**')
    with col4: st.info(f'🟠 Сокращённых: **{len(month_info["short"])}**')
    
    st.markdown('---')
    
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
        'Сотрудник': st.column_config.TextColumn('Сотрудник', width='medium', disabled=True),
        'ИТОГО': st.column_config.NumberColumn('ИТОГО', format='%.1f', width='small', disabled=True),
        'ПЕРЕРАБ': st.column_config.NumberColumn('ПЕРЕРАБ', format='%.1f', width='small', disabled=True),
    }
    
    for day in range(1, days_count + 1):
        if day in cal['holidays']:
            day_label = f'{day}'
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
    
    st.markdown('**💡 Кликай на ячейку и вводи часы. Эмодзи показывают тип дня.**')
    
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
    if st.button('💾 СОХРАНИТЬ ВСЕ ДАННЫЕ', type='primary', use_container_width=True):
        for idx, emp in enumerate(EMPLOYEES):
            if idx < len(edited_df):
                new_hours = [float(edited_df.iloc[idx][str(day)]) for day in range(1, days_count + 1)]
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                save_hours(month, emp, new_hours[:31])
        st.success('✅ Все данные сохранены!')
        st.balloons()
    
    st.markdown('---')
    st.markdown('**📌 Легенда:** 🔴 Праздник |  Сокращённый | 🟣 Выходной | ⚪ Рабочий')
    st.markdown('💡 **Переработка** = всё что больше 8 часов в день')

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
        st.subheader(' Подиум')
        
        if len(df) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;">
                <h2></h2><h3>{df.iloc[1]["Сотрудник"]}</h3>
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
                <h2>🥉</h2><h3>{df.iloc[2]["Сотрудник"]}</h3>
                <p><b>{df.iloc[2]["Часы"]:.1f} ч</b></p>
                <p>Переработка: {df.iloc[2]["Переработка"]:.1f} ч</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('---')
        st.subheader('📋 Полный рейтинг')
        st.dataframe(df, use_container_width=True)
        
        st.markdown('---')
        st.subheader(' Награды месяца')
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
            <h2>📜 АНТИНАГРАДА</h2><h3 style="color:#FFD700;">ЛОХ</h3>
            <p><b>{df.iloc[-1]["Сотрудник"]}</b></p>
            <p>{df.iloc[-1]["Часы"]:.1f} часов | эффективность {df.iloc[-1]["Эффективность %"]:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
