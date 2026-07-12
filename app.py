import streamlit as st
import pandas as pd
import json
from datetime import date, datetime

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

# ============================================
# ИНИЦИАЛИЗАЦИЯ ДАННЫХ
# ============================================
if 'hours_data' not in st.session_state:
    st.session_state.hours_data = {}
if 'feed' not in st.session_state:
    st.session_state.feed = []
if 'votes' not in st.session_state:
    st.session_state.votes = {
        'hardworker': {},  # голоса за работящего
        'slacker': {},     # голоса за халявщика
        'voters': []       # кто уже голосовал
    }
if 'checkins' not in st.session_state:
    st.session_state.checkins = {}  # ежедневные отметки

def get_hours(month, emp):
    key = f"{month}_{emp}"
    if key not in st.session_state.hours_data:
        st.session_state.hours_data[key] = [0.0] * 31
    return st.session_state.hours_data[key]

def save_hours(month, emp, hours):
    key = f"{month}_{emp}"
    st.session_state.hours_data[key] = hours

def add_to_feed(message, emoji='📝'):
    """Добавить запись в ленту активности"""
    now = datetime.now().strftime('%d.%m %H:%M')
    st.session_state.feed.insert(0, {
        'time': now,
        'emoji': emoji,
        'message': message
    })
    # Ограничиваем ленту 50 записями
    if len(st.session_state.feed) > 50:
        st.session_state.feed = st.session_state.feed[:50]

def calc_stats(hours, norm, workdays):
    total = sum(hours)
    overtime = sum(max(0, h - 8) for h in hours if h > 0)
    efficiency = (total / norm * 100) if norm > 0 else 0
    remaining_hours = max(0, norm - total)
    workdays_worked = sum(1 for h in hours if h > 0)
    remaining_days = max(0, workdays - workdays_worked)
    return total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days

def get_checkin_streak(emp):
    """Посчитать серию дней подряд"""
    if emp not in st.session_state.checkins:
        return 0
    return len(st.session_state.checkins[emp])

def mark_checkin(emp, month, day):
    """Отметить ежедневный заход"""
    if emp not in st.session_state.checkins:
        st.session_state.checkins[emp] = []
    entry = f"{month} День {day} ({date.today().strftime('%d.%m')})"
    if entry not in st.session_state.checkins[emp]:
        st.session_state.checkins[emp].append(entry)
        streak = len(st.session_state.checkins[emp])
        add_to_feed(f'{emp} отметил день #{day} в {month}! Серия: {streak} 🔥', '✅')

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title('📊 Учет рабочего времени')

st.sidebar.markdown('### 💾 Управление данными')
data_json = json.dumps({
    'hours': st.session_state.hours_data,
    'feed': st.session_state.feed,
    'votes': st.session_state.votes,
    'checkins': st.session_state.checkins
}, ensure_ascii=False)
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
        st.session_state.hours_data = new_data.get('hours', {})
        st.session_state.feed = new_data.get('feed', [])
        st.session_state.votes = new_data.get('votes', {'hardworker': {}, 'slacker': {}, 'voters': []})
        st.session_state.checkins = new_data.get('checkins', {})
        st.sidebar.success('✅ Данные загружены!')
    except Exception as e:
        st.sidebar.error(f'❌ Ошибка: {e}')

st.sidebar.markdown('---')

page = st.sidebar.radio('Меню', ['dashboard', 'input', 'activity', 'votes', 'rating'])
month = st.sidebar.selectbox('📅 Месяц', MONTHS)

month_info = MONTHS_DATA[month]
norm = month_info['norm']
workdays = month_info['workdays']

st.sidebar.markdown('---')
st.sidebar.markdown(f'** {month} 2026**')
st.sidebar.markdown(f'Рабочих дней: **{workdays}**')
st.sidebar.markdown(f'Норма часов: **{norm}**')

# ============================================
# ДАШБОРД
# ============================================
if page == 'dashboard':
    st.title(f'📊 Дашборд — {month} 2026')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency, remaining_hours, workdays_worked, remaining_days = calc_stats(hours, norm, workdays)
        streak = get_checkin_streak(emp)
        stats_list.append({
            'Сотрудник': emp,
            'Отработано часов': total,
            'Норма часов': norm,
            'Осталось часов': remaining_hours,
            'Процент выполнения': f'{efficiency:.1f}%',
            'Отработано дней': workdays_worked,
            'Рабочих дней в месяце': workdays,
            'Осталось дней': remaining_days,
            'Переработка': overtime,
            'Серия дней 🔥': streak
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
    
    st.markdown('---')
    st.subheader('📊 Детальная статистика по сотрудникам')
    
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
            st.metric('📅 Рабочих дней', f"{row['Отработано дней']} / {workdays}")
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
# ВВОД ЧАСОВ С АВТО-АКТИВНОСТЬЮ
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
            day_label = f'🔴{day}'
        elif day in cal['short']:
            day_label = f'🟠{day}'
        elif day in cal['weekends']:
            day_label = f'{day}'
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
    
    st.markdown('**💡 Кликай на ячейку и вводи часы. Нажми "СОХРАНИТЬ" — запись появится в ленте активности!**')
    
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
                new_hours = []
                total_emp = 0
                days_worked = 0
                for day in range(1, days_count + 1):
                    val = edited_df.iloc[idx][str(day)]
                    try:
                        val = float(val)
                    except:
                        val = 0.0
                    new_hours.append(val)
                    total_emp += val
                    if val > 0:
                        days_worked += 1
                while len(new_hours) < 31:
                    new_hours.append(0.0)
                save_hours(month, emp, new_hours[:31])
                
                # Добавляем запись в ленту
                if total_emp > 0:
                    add_to_feed(
                        f'{emp} проставил часы за {month}: {total_emp:.1f} ч ({days_worked} дн.)',
                        '⏱'
                    )
                    # Отмечаем ежедневный заход
                    mark_checkin(emp, month, days_worked)
        
        st.success('✅ Все данные сохранены! Записи добавлены в ленту активности.')
        st.balloons()
    
    st.markdown('---')
    st.markdown('** Легенда:** 🔴 Праздник |  Сокращённый | 🟣 Выходной | ⚪ Рабочий')
    st.markdown('💡 **Переработка** = всё что больше 8 часов в день')

# ============================================
# ЛЕНТА АКТИВНОСТИ
# ============================================
elif page == 'activity':
    st.title('📱 Лента активности')
    
    st.markdown('**Здесь отображаются все действия сотрудников в реальном времени**')
    st.markdown('---')
    
    # Статистика заходов
    st.subheader('🔥 Ежедневные серии')
    
    checkin_data = []
    for emp in EMPLOYEES:
        streak = get_checkin_streak(emp)
        checkin_data.append({
            'Сотрудник': emp,
            'Серия дней': streak,
            'Статус': ' В игре' if streak > 0 else '😴 Не активен'
        })
    
    df_checkin = pd.DataFrame(checkin_data).sort_values('Серия дней', ascending=False)
    st.dataframe(df_checkin, use_container_width=True, hide_index=True)
    
    st.markdown('---')
    
    # Сама лента
    st.subheader('📰 Последние события')
    
    if len(st.session_state.feed) == 0:
        st.info('📭 Лента пуста. Начни вводить часы — события появятся здесь!')
    else:
        for item in st.session_state.feed:
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px;">{item['emoji']} {item['message']}</span>
                    <span style="font-size: 12px; color: #94a3b8;">{item['time']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('---')
    
    # Кнопка очистки ленты
    if st.button('️ Очистить ленту', use_container_width=True):
        st.session_state.feed = []
        st.success('Лента очищена!')
        st.rerun()

# ============================================
# ГОЛОСОВАНИЯ
# ============================================
elif page == 'votes':
    st.title('🗳️ Голосования недели')
    
    st.markdown('**Проголосуй за самого работящего и главного халявщика команды!**')
    st.markdown('---')
    
    # Выбор кто голосует
    voter = st.selectbox('👤 Кто голосует?', ['— Выбери себя —'] + EMPLOYEES)
    
    if voter == '— Выбери себя —':
        st.warning('⚠️ Выбери своё имя чтобы проголосовать')
    else:
        # Проверяем не голосовал ли уже
        already_voted = voter in st.session_state.votes['voters']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('💪 Самый работящий')
            st.markdown('Кто вкалывал больше всех на этой неделе?')
            
            if already_voted:
                st.info(f'Ты уже голосовал! Твой выбор: {st.session_state.votes["hardworker"].get(voter, "-")}')
            else:
                hardworker_choice = st.radio(
                    'Выбери работящего:',
                    [e for e in EMPLOYEES if e != voter],
                    key='hw_vote'
                )
                if st.button('✅ Голосовать за работящего', type='primary', use_container_width=True):
                    st.session_state.votes['hardworker'][voter] = hardworker_choice
                    st.session_state.votes['voters'].append(voter)
                    add_to_feed(f'{voter} проголосовал за работящего: {hardworker_choice} 💪', '🗳️')
                    st.success(f'Голос засчитан! {hardworker_choice} получает +1 голос')
                    st.rerun()
        
        with col2:
            st.subheader('😴 Главный халявщик')
            st.markdown('Кто больше всех проебался на этой неделе?')
            
            if already_voted:
                st.info(f'Ты уже голосовал! Твой выбор: {st.session_state.votes["slacker"].get(voter, "-")}')
            else:
                slacker_choice = st.radio(
                    'Выбери халявщика:',
                    [e for e in EMPLOYEES if e != voter],
                    key='sl_vote'
                )
                if st.button(' Голосовать за халявщика', type='primary', use_container_width=True):
                    st.session_state.votes['slacker'][voter] = slacker_choice
                    if voter not in st.session_state.votes['voters']:
                        st.session_state.votes['voters'].append(voter)
                    add_to_feed(f'{voter} проголосовал за халявщика: {slacker_choice} 😴', '🗳️')
                    st.success(f'Голос засчитан! {slacker_choice} получает +1 голос')
                    st.rerun()
    
    st.markdown('---')
    
    # Результаты голосования
    st.subheader('📊 Текущие результаты')
    
    # Считаем голоса
    hw_votes = {}
    sl_votes = {}
    for emp in EMPLOYEES:
        hw_votes[emp] = sum(1 for v in st.session_state.votes['hardworker'].values() if v == emp)
        sl_votes[emp] = sum(1 for v in st.session_state.votes['slacker'].values() if v == emp)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('### 💪 Работящий (больше голосов = лучше)')
        hw_df = pd.DataFrame([
            {'Сотрудник': emp, 'Голоса': hw_votes[emp]} 
            for emp in EMPLOYEES
        ]).sort_values('Голоса', ascending=False)
        
        for idx, row in hw_df.iterrows():
            if row['Голоса'] > 0:
                bar = '█' * row['Голоса']
                st.markdown(f'**{row["Сотрудник"]}**: {bar} ({row["Голоса"]})')
            else:
                st.markdown(f'{row["Сотрудник"]}: 0')
    
    with col2:
        st.markdown('### 😴 Халявщик (больше голосов = хуже)')
        sl_df = pd.DataFrame([
            {'Сотрудник': emp, 'Голоса': sl_votes[emp]} 
            for emp in EMPLOYEES
        ]).sort_values('Голоса', ascending=False)
        
        for idx, row in sl_df.iterrows():
            if row['Голоса'] > 0:
                bar = '█' * row['Голоса']
                st.markdown(f'**{row["Сотрудник"]}**: {bar} ({row["Голоса"]})')
            else:
                st.markdown(f'{row["Сотрудник"]}: 0')
    
    st.markdown('---')
    
    # Победители
    top_hw = max(hw_votes, key=hw_votes.get) if any(v > 0 for v in hw_votes.values()) else None
    top_sl = max(sl_votes, key=sl_votes.get) if any(v > 0 for v in sl_votes.values()) else None
    
    if top_hw or top_sl:
        st.subheader('🏆 Лидеры голосования')
        col1, col2 = st.columns(2)
        
        if top_hw and hw_votes[top_hw] > 0:
            with col1:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #10b981, #059669); padding:20px; border-radius:10px; text-align:center;">
                <h2>💪 РАБОТЯГА НЕДЕЛИ</h2>
                <h3>{top_hw}</h3>
                <p>{hw_votes[top_hw]} голос(ов)</p>
                </div>
                """, unsafe_allow_html=True)
        
        if top_sl and sl_votes[top_sl] > 0:
            with col2:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #ef4444, #dc2626); padding:20px; border-radius:10px; text-align:center;">
                <h2>😴 ХАЛЯВЩИК НЕДЕЛИ</h2>
                <h3>{top_sl}</h3>
                <p>{sl_votes[top_sl]} голос(ов)</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('---')
    
    # Сброс голосования
    if st.button('🔄 Начать новое голосование', use_container_width=True):
        st.session_state.votes = {
            'hardworker': {},
            'slacker': {},
            'voters': []
        }
        add_to_feed('Начато новое голосование недели! 🗳️', '🔄')
        st.success('Голосование сброшено!')
        st.rerun()

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
        st.subheader('🏆 Подиум')
        
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
        st.subheader('🏅 Награды месяца')
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
