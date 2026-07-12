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

st.sidebar.title('📊 Учет рабочего времени')

st.sidebar.markdown('### 💾 Управление данными')
data_json = json.dumps(st.session_state.hours_data, ensure_ascii=False)
st.sidebar.download_button(
    label=' Скачать бэкап',
    data=data_json,
    file_name=f'backup_{date.today().strftime("%Y%m%d")}.json',
    mime='application/json',
    use_container_width=True
)

uploaded_file = st.sidebar.file_uploader(' Загрузить бэкап', type=['json'])
if uploaded_file is not None:
    try:
        new_data = json.load(uploaded_file)
        st.session_state.hours_data = new_data
        st.sidebar.success('✅ Данные загружены!')
    except Exception as e:
        st.sidebar.error(f'❌ Ошибка: {e}')

st.sidebar.markdown('---')
page = st.sidebar.radio(' Меню', ['📊 Дашборд', '✏️ Ввод часов', ' Рейтинг'])
month = st.sidebar.selectbox('📅 Месяц', MONTHS)

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
if page == '📊 Дашборд':
    st.title(f'📊 Дашборд — {month} 2026')
    
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
    st.subheader('📊 Прогресс выполнения нормы')
    
    for idx, row in df.iterrows():
        emp = row['Сотрудник']
        hours = row['Отработано часов']
        percent = row['Процент выполнения']
        remaining = row['Осталось часов']
        progress_value = min(hours / norm, 1.0)
        
        st.markdown(f'**{emp}** — {hours:.1f} / {norm} ч ({percent})')
        if remaining > 0:
            st.markdown(f'Осталось: **{remaining:.1f} ч**')
        else:
            st.markdown(f'✅ **Норма выполнена!** Переработка: {row["Переработка"]:.1f} ч')
        
        progress_html = f'''
        <div style="background-color: #2d2d2d; border-radius: 10px; padding: 3px; margin-bottom: 20px;">
            <div style="background-color: #4CAF50; width: {progress_value * 100}%; height: 30px; border-radius: 8px; text-align: center; line-height: 30px; color: white; font-weight: bold;">
                {percent}
            </div>
        </div>
        '''
        st.markdown(progress_html, unsafe_allow_html=True)
    
    st.markdown('---')
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('⏱ Отработанные часы vs Норма')
        if not df.empty:
            st.bar_chart(df.set_index('Сотрудник')[['Отработано часов', 'Норма часов']])
    with col2:
        st.subheader(' Переработка по сотрудникам')
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

# ============================================
# ВВОД ЧАСОВ С ЦВЕТНЫМИ ЯЧЕЙКАМИ ЧЕРЕЗ NUMBER_INPUT
# ============================================
elif page == '✏️ Ввод часов':
    st.title(f'✏️ Ввод часов — {month} 2026')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info(f'📅 Рабочих дней: **{workdays}**')
    with col2: st.info(f'⏱ Норма часов: **{norm}**')
    with col3: st.info(f'🔴 Праздников: **{len(month_info["holidays"])}**')
    with col4: st.info(f'🟠 Сокращённых: **{len(month_info["short"])}**')
    
    st.markdown('---')
    
    cal = month_info
    year = 2026
    month_num = MONTH_NUM[month]
    days_count = DAYS_IN_MONTH[month]
    
    # CSS для цветных ячеек number_input
    st.markdown("""
    <style>
    /* Стили для контейнеров ячеек */
    .cell-container {
        padding: 2px;
        border-radius: 4px;
        margin: 1px;
    }
    .cell-workday {
        background-color: #1e293b;
    }
    .cell-weekend {
        background-color: #E9D5FF !important;
    }
    .cell-holiday {
        background-color: #FCA5A5 !important;
    }
    .cell-short {
        background-color: #FED7AA !important;
    }
    .cell-total {
        background-color: #86EFAC !important;
        padding: 8px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        color: #064E3B;
    }
    .cell-overtime {
        background-color: #FDE047 !important;
        padding: 8px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        color: #713F12;
    }
    /* Уменьшаем размер number_input */
    .cell-container .stNumberInput {
        min-height: auto;
    }
    .cell-container .stNumberInput input {
        padding: 2px 4px;
        font-size: 11px;
        text-align: center;
    }
    /* Скрываем label number_input */
    .cell-container label {
        display: none;
    }
    /* Контейнер для строки сотрудника */
    .employee-row {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
        padding: 5px;
        background-color: #2d2d2d;
        border-radius: 8px;
    }
    .employee-name {
        min-width: 120px;
        font-weight: bold;
        color: white;
        padding: 0 10px;
    }
    .day-cells {
        display: flex;
        flex-wrap: wrap;
        gap: 2px;
        flex: 1;
    }
    .day-cell {
        width: 40px;
    }
    .totals {
        display: flex;
        gap: 10px;
        margin-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('**💡 Кликай на цветную ячейку и вводи часы. Ячейки окрашены по типу дня.**')
    
    # Форма для сохранения
    with st.form('hours_form'):
        for emp in EMPLOYEES:
            hours = get_hours(month, emp)
            
            # Начало строки сотрудника
            st.markdown(f'<div class="employee-row">', unsafe_allow_html=True)
            st.markdown(f'<div class="employee-name">{emp}</div>', unsafe_allow_html=True)
            st.markdown('<div class="day-cells">', unsafe_allow_html=True)
            
            # Ячейки для каждого дня
            day_values = {}
            for day in range(1, days_count + 1):
                h = float(hours[day-1]) if day-1 < len(hours) else 0.0
                
                # Определяем тип дня и класс
                if day in cal['holidays']:
                    cell_class = 'cell-holiday'
                elif day in cal['short']:
                    cell_class = 'cell-short'
                elif day in cal['weekends']:
                    cell_class = 'cell-weekend'
                else:
                    cell_class = 'cell-workday'
                
                # Контейнер с цветом
                st.markdown(f'<div class="cell-container {cell_class} day-cell">', unsafe_allow_html=True)
                
                # Number input
                key = f'{emp}_day{day}'
                val = st.number_input(
                    '',
                    min_value=0.0,
                    max_value=24.0,
                    value=h,
                    step=0.5,
                    key=key,
                    label_visibility='collapsed'
                )
                day_values[day] = val
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ИТОГО и ПЕРЕРАБ
            total = sum(day_values.values())
            overtime = sum(max(0, v - 8) for v in day_values.values() if v > 0)
            
            st.markdown('<div class="totals">', unsafe_allow_html=True)
            st.markdown(f'<div class="cell-total">ИТОГО: {total:.1f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cell-overtime">ПЕРЕРАБ: {overtime:.1f}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Кнопка сохранения
        submitted = st.form_submit_button('💾 СОХРАНИТЬ ВСЕ ДАННЫЕ', type='primary', use_container_width=True)
        
        if submitted:
            # Сохраняем данные из формы
            for emp in EMPLOYEES:
                new_hours = []
                for day in range(1, days_count + 1):
                    key = f'{emp}_day{day}'
                    val = st.session_state.get(key, 0.0)
                    try:
                        val = float(val)
                    except:
                        val = 0.0
                    new_hours.append(val)
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                save_hours(month, emp, new_hours[:31])
            st.success('✅ Все данные сохранены!')
            st.rerun()
    
    # Легенда
    st.markdown('---')
    st.markdown('**📌 Легенда цветов ячеек:**')
    st.markdown('''
    <span style="background-color: #FCA5A5; color: #991B1B; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;"> Праздник</span>
    <span style="background-color: #FED7AA; color: #9A3412; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">🟠 Сокращённый</span>
    <span style="background-color: #E9D5FF; color: #6B21A8; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">💜 Выходной</span>
    <span style="background-color: #1e293b; color: white; display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 5px; font-size: 12px;">⚪ Рабочий</span>
    ''', unsafe_allow_html=True)
    
    st.markdown('💡 **Переработка** = всё что больше 8 часов в день')

# ============================================
# РЕЙТИНГ
# ============================================
elif page == '🏆 Рейтинг':
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
        st.warning('️ Нет данных за этот месяц. Введите часы на странице "Ввод часов".')
    else:
        st.markdown('---')
        st.subheader('🏆 Подиум')
        
        if len(df) >= 3:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'''
                <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;">
                <h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3>
                <p><b>{df.iloc[1]["Часы"]:.1f} ч</b></p>
                <p>Переработка: {df.iloc[1]["Переработка"]:.1f} ч</p>
                </div>
                ''', unsafe_allow_html=True)
            with col2:
                st.markdown(f'''
                <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:30px; border-radius:10px; text-align:center; border:3px solid gold;">
                <h1>🥇</h1><h2>{df.iloc[0]["Сотрудник"]}</h2>
                <p style="font-size:24px
