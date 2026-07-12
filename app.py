import streamlit as st
import pandas as pd
from datetime import date

# ============================================
# НАСТРОЙКИ СТРАНИЦЫ
# ============================================
st.set_page_config(
    page_title="Учёт рабочего времени",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ДАННЫЕ И КАЛЕНДАРЬ
# ============================================
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

def calc_stats(hours, norm, workdays):
    total = sum(hours)
    overtime = sum(max(0, h - 8) for h in hours if h > 0)
    efficiency = (total / norm * 100) if norm > 0 else 0
    remaining_hours = max(0, norm - total)
    workdays_worked = sum(1 for h in hours if h > 0)
    remaining_days = max(0, workdays - workdays_worked)
    return total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title('📊 Учет рабочего времени')
page = st.sidebar.radio(' Меню', ['📊 Дашборд', '✏️ Ввод часов', ' Рейтинг'])
month = st.sidebar.selectbox('📅 Месяц', MONTHS)

month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

st.sidebar.markdown('---')
st.sidebar.markdown(f'**📅 {month} 2026**')
st.sidebar.markdown(f'Рабочих дней: **{workdays}**')
st.sidebar.markdown(f'Норма часов: **{norm}**')
st.sidebar.markdown(f'Праздники: {len(month_info["holidays"])}')
st.sidebar.markdown(f'Сокращённые: {len(month_info["short"])}')

# ============================================
# СТРАНИЦА 1: ДАШБОРД
# ============================================
if page == '📊 Дашборд':
    st.title(f' Дашборд — {month} 2026')
    
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
        st.subheader(' Отработанные часы vs Норма')
        if not df.empty:
            chart_data = df.set_index('Сотрудник')[['Отработано часов', 'Норма часов']]
            st.bar_chart(chart_data)
    
    with col2:
        st.subheader('🔥 Переработка по сотрудникам')
        if not df.empty:
            chart_data = df.set_index('Сотрудник')['Переработка']
            st.bar_chart(chart_data)
    
    st.markdown('---')
    
    st.subheader('🏆 Статистика')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_worker = df.loc[df['Отработано часов'].idxmax()]
        st.metric('🏆 Лидер месяца', top_worker['Сотрудник'], f"{top_worker['Отработано часов']:.1f} ч")
    
    with col2:
        total_overtime = df['Переработка'].sum()
        st.metric('🔥 Всего переработок', f'{total_overtime:.1f} ч')
    
    with col3:
        completed = len(df[df['Осталось часов'] == 0])
        st.metric('✅ Выполнили норму', f'{completed} чел.')

# ============================================
# СТРАНИЦА 2: ВВОД ЧАСОВ (С ЯРКИМИ ЦВЕТАМИ)
# ============================================
elif page == '✏️ Ввод часов':
    st.title(f'✏️ Ввод часов — {month} 2026')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f'📅 Рабочих дней: **{workdays}**')
    with col2:
        st.info(f'⏱ Норма часов: **{norm}**')
    with col3:
        st.info(f'🔴 Праздников: **{len(month_info["holidays"])}**')
    with col4:
        st.info(f'🟠 Сокращённых: **{len(month_info["short"])}**')
    
    st.markdown('---')
    
    cal = month_info
    year = 2026
    month_num = MONTH_NUM[month]
    days_count = DAYS_IN_MONTH[month]
    
    # CSS для ярких цветов ячеек
    st.markdown("""
    <style>
    .time-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 12px;
    }
    .time-table th, .time-table td {
        border: 1px solid #333;
        padding: 4px;
        text-align: center;
        min-width: 30px;
    }
    .time-table th {
        background-color: #1a1a1a;
        color: white;
        font-weight: bold;
        position: sticky;
        top: 0;
    }
    .time-table td.employee-name {
        background-color: #2d2d2d;
        color: white;
        font-weight: bold;
        text-align: left;
        padding: 8px;
        min-width: 120px;
    }
    .time-table td.workday {
        background-color: #ffffff;
        color: #000000;
    }
    .time-table td.weekend {
        background-color: #FF6B6B !important;
        color: #000000 !important;
        font-weight: bold;
    }
    .time-table td.holiday {
        background-color: #FF0000 !important;
        color: #FFFFFF !important;
        font-weight: bold;
    }
    .time-table td.short {
        background-color: #FFA500 !important;
        color: #000000 !important;
        font-weight: bold;
    }
    .time-table td.total {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .time-table td.overtime {
        background-color: #FFD700;
        color: #000000;
        font-weight: bold;
    }
    .time-table input {
        width: 100%;
        border: none;
        background: transparent;
        text-align: center;
        font-size: 12px;
        color: inherit;
    }
    .time-table input:focus {
        outline: 2px solid #2196F3;
        background: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Собираем данные для таблицы
    emp_data = {}
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        emp_data[emp] = hours
    
    # Создаём HTML таблицу
    html_table = '<table class="time-table">'
    
    # Заголовок
    html_table += '<tr><th>Сотрудник</th>'
    for day in range(1, days_count + 1):
        if day in cal['holidays']:
            html_table += f'<th style="background-color: #FF0000; color: white;">{day}</th>'
        elif day in cal['short']:
            html_table += f'<th style="background-color: #FFA500; color: black;">{day}</th>'
        elif day in cal['weekends']:
            html_table += f'<th style="background-color: #FF6B6B; color: black;">{day}</th>'
        else:
            html_table += f'<th>{day}</th>'
    html_table += '<th style="background-color: #4CAF50;">ИТОГО</th>'
    html_table += '<th style="background-color: #FFD700; color: black;">ПЕРЕРАБ</th>'
    html_table += '</tr>'
    
    # Строки сотрудников
    for emp in EMPLOYEES:
        hours = emp_data[emp]
        html_table += f'<tr><td class="employee-name">{emp}</td>'
        
        total = 0
        overtime = 0
        
        for day in range(1, days_count + 1):
            h = hours[day-1] if day-1 < len(hours) else 0.0
            total += h
            if h > 0:
                overtime += max(0, h - 8)
            
            # Определяем класс ячейки
            if day in cal['holidays']:
                cell_class = 'holiday'
            elif day in cal['short']:
                cell_class = 'short'
            elif day in cal['weekends']:
                cell_class = 'weekend'
            else:
                cell_class = 'workday'
            
            html_table += f'<td class="{cell_class}"><input type="number" step="0.5" min="0" max="24" value="{h:.1f}" data-emp="{emp}" data-day="{day}"></td>'
        
        html_table += f'<td class="total">{total:.1f}</td>'
        html_table += f'<td class="overtime">{overtime:.1f}</td>'
        html_table += '</tr>'
    
    html_table += '</table>'
    
    st.markdown(html_table, unsafe_allow_html=True)
    
    st.markdown('---')
    st.markdown('** Легенда:**')
    st.markdown('🔴 **Красный** — Праздник | 🟠 **Оранжевый** — Сокращённый |  **Розовый** — Выходной')
    st.markdown('💡 Кликай на ячейку и вводи часы. Нажми "Сохранить" когда закончишь.')
    
    # Кнопка сохранения (упрощённая версия)
    if st.button('💾 СОХРАНИТЬ', type='primary', use_container_width=True):
        st.warning('⚠️ Используй форму ввода ниже для сохранения данных')
    
    # Форма для ввода часов (резервный вариант)
    st.markdown('---')
    st.subheader('📝 Форма ввода часов')
    
    selected_emp = st.selectbox('Выбери сотрудника', EMPLOYEES)
    hours = get_hours(month, selected_emp)
    
    new_hours = []
    for week in range(5):
        st.markdown(f'**Неделя {week + 1}**')
        cols = st.columns(7)
        for i in range(7):
            day = week * 7 + i + 1
            if day > days_count:
                break
            
            if day in cal['holidays']:
                day_label = f'🔴 День {day}'
            elif day in cal['short']:
                day_label = f'🟠 День {day}'
            elif day in cal['weekends']:
                day_label = f'⚪ День {day}'
            else:
                day_label = f'День {day}'
            
            val = cols[i].number_input(
                day_label,
                min_value=0.0,
                max_value=24.0,
                value=float(hours[day-1]),
                step=0.5,
                key=f'{selected_emp}_day{day}'
            )
            new_hours.append(val)
    
    while len(new_hours) < 31:
        new_hours.append(0.0)
    
    if st.button('💾 СОХРАНИТЬ ДАННЫЕ', type='primary', use_container_width=True):
        save_hours(month, selected_emp, new_hours[:31])
        st.success(f'✅ Данные для {selected_emp} сохранены!')
        st.rerun()

# ============================================
# СТРАНИЦА 3: РЕЙТИНГ
# ============================================
elif page == ' Рейтинг':
    st.title(f' Рейтинг — {month}')
    
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
                <h1></h1>
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
        st.subheader('📋 Полный рейтинг')
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
