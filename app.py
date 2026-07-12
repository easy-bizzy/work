import streamlit as st
import pandas as pd
import json
from datetime import date

st.set_page_config(
    page_title="Учёт рабочего времени",
    page_icon="",
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
page = st.sidebar.radio('📋 Меню', ['📊 Дашборд', '✏️ Ввод часов', '🏆 Рейтинг'])
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
if page == ' Дашборд':
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
    
    st.subheader(' Статистика по каждому сотруднику')
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
        st.subheader('🔥 Переработка по сотрудникам')
        if not df.empty:
            st.bar_chart(df.set_index('Сотрудник')['Переработка'])
    
    st.markdown('---')
    st.subheader('🏆 Статистика')
    col1, col2, col3 = st.columns(3)
    with col1:
        top_worker = df.loc[df['Отработано часов'].idxmax()]
        st.metric(' Лидер месяца', top_worker['Сотрудник'], f"{top_worker['Отработано часов']:.1f} ч")
    with col2:
        st.metric('🔥 Всего переработок', f"{df['Переработка'].sum():.1f} ч")
    with col3:
        completed = len(df[df['Осталось часов'] == 0])
        st.metric('✅ Выполнили норму', f'{completed} чел.')

# ============================================
# ВВОД ЧАСОВ (УПРОЩЁННАЯ ВЕРСИЯ)
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
    days_count = DAYS_IN_MONTH[month]
    
    # Легенда
    st.markdown('**📌 Легенда:**')
    st.markdown('🔴 **Красный** — Праздник | 🟠 **Оранжевый** — Сокращённый | 🟣 **Фиолетовый** — Выходной | ⚪ **Обычный** — Рабочий')
    
    st.markdown('---')
    
    # Ввод по сотрудникам
    for emp in EMPLOYEES:
        st.subheader(f'👤 {emp}')
        hours = get_hours(month, emp)
        
        # Создаём колонки для дней (по 7 в ряд - неделя)
        day_values = {}
        
        for week in range(5):  # 5 недель
            week_days = []
            for day_in_week in range(7):
                day = week * 7 + day_in_week + 1
                if day > days_count:
                    break
                week_days.append(day)
            
            if not week_days:
                break
            
            # Заголовки дней
            cols = st.columns(len(week_days) + 1)  # +1 для метки недели
            
            # Метка недели
            with cols[0]:
                st.markdown(f'**Нед {week+1}**')
            
            # Ячейки дней
            for i, day in enumerate(week_days):
                h = float(hours[day-1]) if day-1 < len(hours) else 0.0
                
                # Определяем тип дня
                if day in cal['holidays']:
                    day_label = f'🔴{day}'
                elif day in cal['short']:
                    day_label = f'🟠{day}'
                elif day in cal['weekends']:
                    day_label = f'🟣{day}'
                else:
                    day_label = str(day)
                
                with cols[i + 1]:
                    key = f'{emp}_day{day}'
                    val = st.number_input(
                        day_label,
                        min_value=0.0,
                        max_value=24.0,
                        value=h,
                        step=0.5,
                        key=key
                    )
                    day_values[day] = val
        
        # ИТОГО и ПЕРЕРАБ
        total = sum(day_values.values())
        overtime = sum(max(0, v - 8) for v in day_values.values() if v > 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f'**ИТОГО: {total:.1f} ч**')
        with col2:
            st.warning(f'**ПЕРЕРАБОТКА: {overtime:.1f} ч**')
        
        st.markdown('---')
    
    # Кнопка сохранения
    if st.button('💾 СОХРАНИТЬ ВСЕ ДАННЫЕ', type='primary', use_container_width=True):
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
        st.balloons()

# ============================================
# РЕЙТИНГ
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
                st.markdown(f"""
                <div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;">
                <h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3>
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
        st.subheader('🏅 Награды месяца')
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #FFD700, #FFA500); padding:20px; border-radius:10px; border:2px solid gold;">
            <h2> ГРАМОТА</h2><h3 style="color:#000;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3>
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
