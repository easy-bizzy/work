import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# ============================================
# НАСТРОЙКИ СТРАНИЦЫ
# ============================================
st.set_page_config(
    page_title="🏆 Учёт времени - Оазис",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ДАННЫЕ
# ============================================
EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']

MONTHS_DATA = {
    'ИЮЛЬ': {'days': 23, 'norm': 184, 'weekends': [4,5,11,12,18,19,25,26], 'holidays': [], 'short': []},
    'АВГУСТ': {'days': 21, 'norm': 168, 'weekends': [1,2,8,9,15,16,22,23,29,30], 'holidays': [], 'short': []},
    'СЕНТЯБРЬ': {'days': 22, 'norm': 176, 'weekends': [5,6,12,13,19,20,26,27], 'holidays': [], 'short': []},
    'ОКТЯБРЬ': {'days': 22, 'norm': 176, 'weekends': [3,4,10,11,17,18,24,25,31], 'holidays': [], 'short': []},
    'НОЯБРЬ': {'days': 20, 'norm': 160, 'weekends': [1,7,8,14,15,21,22,28,29], 'holidays': [4], 'short': [3]},
    'ДЕКАБРЬ': {'days': 23, 'norm': 184, 'weekends': [5,6,12,13,19,20,26,27], 'holidays': [], 'short': [31]},
}

# Геймификация: уровни
LEVELS = [
    (0, '🌱 Новичок'),
    (500, '⚡ Рабочий'),
    (1000, '🔥 Трудяга'),
    (1500, '🤖 Машина'),
    (2000, '🏆 Легенда'),
]

# Достижения
ACHIEVEMENTS = [
    ('first_overtime', '💪 Первая переработка', 'Первый раз переработал больше 0 часов'),
    ('perfect_month', '🎯 Идеальный месяц', '100% выполнение нормы без переработок'),
    ('workaholic', ' Трудоголик', 'Переработка больше 30 часов за месяц'),
    ('machine', '🤖 Машина', 'Переработка больше 50 часов за месяц'),
    ('legend', '👑 Легенда', 'Набрал 2000+ XP'),
    ('consistent', ' Стабильность', '3 месяца подряд в топ-3'),
]

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
# ============================================
def load_data():
    """Загрузка данных из JSON файла"""
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'hours': {}, 'achievements': {}, 'xp': {}}

def save_data(data):
    """Сохранение данных в JSON файл"""
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_month_data(data, month, emp):
    """Получить данные сотрудника за месяц"""
    key = f"{month}_{emp}"
    if key in data['hours']:
        return data['hours'][key]
    return [0] * 31

def save_month_data(data, month, emp, hours_list):
    """Сохранить данные сотрудника за месяц"""
    key = f"{month}_{emp}"
    data['hours'][key] = hours_list
    save_data(data)

def calculate_stats(hours_list, norm):
    """Подсчёт статистики"""
    total = sum(hours_list)
    overtime = sum(max(0, h - 8) for h in hours_list)
    workdays = sum(1 for h in hours_list if h > 0)
    efficiency = (total / norm * 100) if norm > 0 else 0
    return {
        'total': total,
        'overtime': overtime,
        'workdays': workdays,
        'efficiency': efficiency,
    }

def get_level(xp):
    """Определить уровень по XP"""
    level = LEVELS[0][1]
    for threshold, name in LEVELS:
        if xp >= threshold:
            level = name
    return level

def get_xp(stats):
    """Рассчитать XP за месяц"""
    xp = 0
    xp += stats['total'] * 2  # 2 XP за каждый час
    xp += stats['overtime'] * 3  # бонус за переработку
    if stats['efficiency'] >= 100:
        xp += 50  # бонус за выполнение нормы
    return xp

def check_achievements(data, emp, month, stats):
    """Проверить достижения"""
    new_achievements = []
    emp_key = emp
    
    if emp_key not in data['achievements']:
        data['achievements'][emp_key] = []
    
    # Первая переработка
    if stats['overtime'] > 0 and 'first_overtime' not in data['achievements'][emp_key]:
        data['achievements'][emp_key].append('first_overtime')
        new_achievements.append('💪 Первая переработка')
    
    # Идеальный месяц
    if 95 <= stats['efficiency'] <= 105 and 'perfect_month' not in data['achievements'][emp_key]:
        data['achievements'][emp_key].append('perfect_month')
        new_achievements.append('🎯 Идеальный месяц')
    
    # Трудоголик
    if stats['overtime'] > 30 and 'workaholic' not in data['achievements'][emp_key]:
        data['achievements'][emp_key].append('workaholic')
        new_achievements.append('🔥 Трудоголик')
    
    # Машина
    if stats['overtime'] > 50 and 'machine' not in data['achievements'][emp_key]:
        data['achievements'][emp_key].append('machine')
        new_achievements.append('🤖 Машина')
    
    return new_achievements

# ============================================
# БОКОВАЯ ПАНЕЛЬ
# ============================================
st.sidebar.title('🏆 ОАЗИС')
st.sidebar.markdown('---')

page = st.sidebar.radio(
    '📋 Навигация',
    ['📊 Дашборд', '✏️ Ввод часов', '🏆 Рейтинг', '🎮 Геймификация', '📈 Аналитика']
)

selected_month = st.sidebar.selectbox('📅 Месяц', list(MONTHS_DATA.keys()))
month_info = MONTHS_DATA[selected_month]

st.sidebar.markdown('---')
st.sidebar.info(f"**{selected_month} 2026**\n\nРД: {month_info['days']}\nНорма: {month_info['norm']} ч")

# ============================================
# ЗАГРУЗКА ДАННЫХ
# ============================================
data = load_data()

# ============================================
# СТРАНИЦА 1: ДАШБОРД
# ============================================
if page == '📊 Дашборд':
    st.title('📊 Дашборд')
    st.markdown(f'### {selected_month} 2026')
    
    # Собираем статистику по всем сотрудникам
    all_stats = []
    for emp in EMPLOYEES:
        hours = get_month_data(data, selected_month, emp)
        stats = calculate_stats(hours, month_info['norm'])
        stats['name'] = emp
        all_stats.append(stats)
    
    df = pd.DataFrame(all_stats)
    
    # KPI карточки
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_hours = df['total'].sum()
        st.metric('⏱ Всего часов', f'{total_hours:.1f}')
    
    with col2:
        total_overtime = df['overtime'].sum()
        st.metric('🔥 Переработка', f'{total_overtime:.1f} ч')
    
    with col3:
        avg_efficiency = df['efficiency'].mean()
        st.metric('📈 Средняя эффективность', f'{avg_efficiency:.0f}%')
    
    with col4:
        top_worker = df.loc[df['total'].idxmax()]
        st.metric('🏆 Лидер', top_worker['name'])
    
    st.markdown('---')
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('⏱ Часы по сотрудникам')
        fig_hours = px.bar(
            df, x='name', y='total',
            color='name',
            title='Общее количество часов',
            labels={'name': 'Сотрудник', 'total': 'Часы'}
        )
        fig_hours.update_layout(showlegend=False)
        st.plotly_chart(fig_hours, use_container_width=True)
    
    with col2:
        st.subheader(' Переработка')
        fig_overtime = px.bar(
            df, x='name', y='overtime',
            color='overtime',
            color_continuous_scale=['green', 'yellow', 'red'],
            title='Часы переработки',
            labels={'name': 'Сотрудник', 'overtime': 'Переработка'}
        )
        st.plotly_chart(fig_overtime, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('📈 Эффективность')
        fig_eff = px.bar(
            df, x='name', y='efficiency',
            color='efficiency',
            color_continuous_scale=['red', 'yellow', 'green'],
            title='% выполнения нормы',
            labels={'name': 'Сотрудник', 'efficiency': 'Эффективность %'}
        )
        # Линия нормы
        fig_eff.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Норма 100%")
        st.plotly_chart(fig_eff, use_container_width=True)
    
    with col2:
        st.subheader('🎯 Статусы')
        def get_status(row):
            if row['overtime'] == 0:
                return 'БАЛАНС'
            elif row['overtime'] <= 10:
                return 'РАБОЧИЙ'
            elif row['overtime'] <= 30:
                return 'ТРУЖЕНИК'
            else:
                return 'МАШИНА'
        
        df['status'] = df.apply(get_status, axis=1)
        status_counts = df['status'].value_counts()
        
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Распределение статусов',
            color_discrete_map={
                'БАЛАНС': '#27AE60',
                'РАБОЧИЙ': '#3498DB',
                'ТРУЖЕНИК': '#F39C12',
                'МАШИНА': '#E74C3C'
            }
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Таблица с данными
    st.subheader('📋 Сводная таблица')
    display_df = df[['name', 'total', 'overtime', 'efficiency', 'status']].copy()
    display_df.columns = ['Сотрудник', 'Часы', 'Переработка', 'Эффективность %', 'Статус']
    display_df['Эффективность %'] = display_df['Эффективность %'].round(1)
    display_df['Часы'] = display_df['Часы'].round(1)
    display_df['Переработка'] = display_df['Переработка'].round(1)
    st.dataframe(display_df, use_container_width=True)

# ============================================
# СТРАНИЦА 2: ВВОД ЧАСОВ
# ============================================
elif page == '✏️ Ввод часов':
    st.title('✏️ Ввод часов')
    st.markdown(f'### {selected_month} 2026')
    
    # Легенда
    st.markdown('**Легенда:** ⚪ Выходной | 🔴 Праздник |  Сокращённый')
    
    selected_emp = st.selectbox('👤 Сотрудник', EMPLOYEES)
    
    hours = get_month_data(data, selected_month, selected_emp)
    
    # Создаём таблицу ввода
    st.markdown('---')
    st.subheader(f'Часы для: {selected_emp}')
    
    # Группируем дни по неделям
    days_in_month = 31
    
    # Создаём DataFrame для редактирования
    input_data = []
    for day in range(1, days_in_month + 1):
        day_type = 'Рабочий'
        if day in month_info['holidays']:
            day_type = '🔴 Праздник'
        elif day in month_info['short']:
            day_type = '🟠 Сокращённый'
        elif day in month_info['weekends']:
            day_type = '⚪ Выходной'
        
        input_data.append({
            'День': day,
            'Тип': day_type,
            'Часы': hours[day-1] if day-1 < len(hours) else 0
        })
    
    df_input = pd.DataFrame(input_data)
    
    # Редактируемая таблица
    edited_df = st.data_editor(
        df_input,
        column_config={
            'День': st.column_config.NumberColumn('День', min_value=1, max_value=31, disabled=True),
            'Тип': st.column_config.TextColumn('Тип дня', disabled=True),
            'Часы': st.column_config.NumberColumn('Часы', min_value=0, max_value=24, step=0.5),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Кнопка сохранения
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(' Сохранить', type='primary', use_container_width=True):
            new_hours = edited_df['Часы'].tolist()
            save_month_data(data, selected_month, selected_emp, new_hours)
            st.success('✅ Данные сохранены!')
            st.rerun()
    
    # Статистика по сотруднику
    st.markdown('---')
    st.subheader('📊 Твоя статистика')
    
    stats = calculate_stats(hours, month_info['norm'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(' Всего часов', f'{stats["total"]:.1f}')
    with col2:
        st.metric('🔥 Переработка', f'{stats["overtime"]:.1f} ч')
    with col3:
        st.metric(' Эффективность', f'{stats["efficiency"]:.0f}%')
    with col4:
        st.metric('📅 Рабочих дней', stats['workdays'])
    
    # График по дням
    st.subheader(' Часы по дням')
    fig_daily = px.bar(
        x=[f'День {i+1}' for i in range(days_in_month)],
        y=hours,
        title=f'Часы по дням - {selected_emp}',
        labels={'x': 'День', 'y': 'Часы'}
    )
    fig_daily.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Норма 8ч")
    st.plotly_chart(fig_daily, use_container_width=True)

# ============================================
# СТРАНИЦА 3: РЕЙТИНГ
# ============================================
elif page == '🏆 Рейтинг':
    st.title('🏆 Рейтинг месяца')
    st.markdown(f'### {selected_month} 2026')
    
    # Собираем статистику
    all_stats = []
    for emp in EMPLOYEES:
        hours = get_month_data(data, selected_month, emp)
        stats = calculate_stats(hours, month_info['norm'])
        stats['name'] = emp
        all_stats.append(stats)
    
    df = pd.DataFrame(all_stats)
    df = df.sort_values('total', ascending=False).reset_index(drop=True)
    df['place'] = range(1, len(df) + 1)
    
    # Подиум
    st.markdown('---')
    st.subheader(' Подиум')
    
    col1, col2, col3 = st.columns(3)
    
    # 2 место
    with col1:
        if len(df) >= 2:
            row = df.iloc[1]
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #C0C0C0, #E8E8E8); padding: 20px; border-radius: 10px; text-align: center;">
                <h2>🥈</h2>
                <h3>{row["name"]}</h3>
                <p><b>{row["total"]:.1f} ч</b></p>
                <p>Переработка: {row["overtime"]:.1f} ч</p>
            </div>
            ''', unsafe_allow_html=True)
    
    # 1 место
    with col2:
        if len(df) >= 1:
            row = df.iloc[0]
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #FFD700, #FFF8DC); padding: 30px; border-radius: 10px; text-align: center; border: 3px solid gold;">
                <h1>🥇</h1>
                <h2>{row["name"]}</h2>
                <p style="font-size: 24px;"><b>{row["total"]:.1f} ч</b></p>
                <p>Переработка: {row["overtime"]:.1f} ч</p>
                <p style="color: gold; font-size: 18px;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p>
            </div>
            ''', unsafe_allow_html=True)
    
    # 3 место
    with col3:
        if len(df) >= 3:
            row = df.iloc[2]
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #CD7F32, #E8C4A0); padding: 20px; border-radius: 10px; text-align: center;">
                <h2></h2>
                <h3>{row["name"]}</h3>
                <p><b>{row["total"]:.1f} ч</b></p>
                <p>Переработка: {row["overtime"]:.1f} ч</p>
            </div>
            ''', unsafe_allow_html=True)
    
    # Полная таблица
    st.markdown('---')
    st.subheader('📋 Полный рейтинг')
    
    display_df = df[['place', 'name', 'total', 'overtime', 'efficiency']].copy()
    display_df.columns = ['Место', 'Сотрудник', 'Часы', 'Переработка', 'Эффективность %']
    display_df['Эффективность %'] = display_df['Эффективность %'].round(1)
    display_df['Часы'] = display_df['Часы'].round(1)
    display_df['Переработка'] = display_df['Переработка'].round(1)
    
    st.dataframe(display_df, use_container_width=True)
    
    # Награды
    st.markdown('---')
    st.subheader(' Награды месяца')
    
    col1, col2 = st.columns(2)
    
    with col1:
        winner = df.iloc[0]
        st.markdown(f'''
        <div style="background: linear-gradient(135deg, #FFD700, #FFF8DC); padding: 20px; border-radius: 10px; border: 3px solid gold;">
            <h2>🏆 ГРАМОТА</h2>
            <h3 style="color: gold;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3>
            <p><b>{winner["name"]}</b></p>
            <p>{winner["total"]:.1f} часов | {winner["overtime"]:.1f} ч переработки</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        loser = df.iloc[-1]
        st.markdown(f'''
        <div style="background: linear-gradient(135deg, #8B4513, #D2B48C); padding: 20px; border-radius: 10px; border: 3px solid #8B4513;">
            <h2>📜 АНТИНАГРАДА</h2>
            <h3 style="color: #8B4513;">ЛОХ</h3>
            <p><b>{loser["name"]}</b></p>
            <p>{loser["total"]:.1f} часов | эффективность {loser["efficiency"]:.0f}%</p>
        </div>
        ''', unsafe_allow_html=True)

# ============================================
# СТРАНИЦА 4: ГЕЙМИФИКАЦИЯ
# ============================================
elif page == '🎮 Геймификация':
    st.title('🎮 Геймификация')
    
    selected_emp = st.selectbox(' Выбери сотрудника', EMPLOYEES)
    
    # Подсчёт общего XP
    total_xp = 0
    total_overtime = 0
    months_participated = 0
    
    for month in MONTHS_DATA.keys():
        hours = get_month_data(data, month, selected_emp)
        if sum(hours) > 0:
            stats = calculate_stats(hours, MONTHS_DATA[month]['norm'])
            total_xp += get_xp(stats)
            total_overtime += stats['overtime']
            months_participated += 1
    
    # Сохраняем XP
    if selected_emp not in data['xp']:
        data['xp'][selected_emp] = 0
    data['xp'][selected_emp] = total_xp
    save_data(data)
    
    # Уровень
    level = get_level(total_xp)
    
    # Прогресс до следующего уровня
    next_level = None
    current_threshold = 0
    for threshold, name in LEVELS:
        if total_xp >= threshold:
            current_threshold = threshold
        else:
            next_level = name
            next_threshold = threshold
            break
    
    progress = ((total_xp - current_threshold) / (next_threshold - current_threshold) * 100) if next_level else 100
    
    st.markdown('---')
    
    # Карточка игрока
    st.subheader(f'🎮 Профиль: {selected_emp}')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric('⭐ Уровень', level)
    
    with col2:
        st.metric('✨ XP', total_xp)
    
    with col3:
        st.metric('🔥 Всего переработок', f'{total_overtime:.1f} ч')
    
    with col4:
        st.metric('📅 Месяцев', months_participated)
    
    # Прогресс-бар
    if next_level:
        st.markdown(f'**Прогресс до следующего уровня: {next_level}**')
        st.progress(progress / 100)
        st.markdown(f'{total_xp} / {next_threshold} XP ({progress:.0f}%)')
    else:
        st.success('🏆 Максимальный уровень достигнут!')
    
    # Достижения
    st.markdown('---')
    st.subheader('🏆 Достижения')
    
    emp_achievements = data['achievements'].get(selected_emp, [])
    
    col1, col2, col3 = st.columns(3)
    
    for i, (ach_id, ach_name, ach_desc) in enumerate(ACHIEVEMENTS):
        unlocked = ach_id in emp_achievements
        col = [col1, col2, col3][i % 3]
        with col:
            if unlocked:
                st.success(f'**{ach_name}**\n\n{ach_desc}')
            else:
                st.info(f'🔒 {ach_name}\n\n{ach_desc}')
    
    # Таблица лидеров по XP
    st.markdown('---')
    st.subheader('🏆 Таблица лидеров по XP')
    
    xp_data = []
    for emp in EMPLOYEES:
        xp = data['xp'].get(emp, 0)
        level = get_level(xp)
        xp_data.append({'Сотрудник': emp, 'XP': xp, 'Уровень': level})
    
    df_xp = pd.DataFrame(xp_data).sort_values('XP', ascending=False).reset_index(drop=True)
    df_xp.index = df_xp.index + 1
    df_xp.index.name = 'Место'
    st.dataframe(df_xp, use_container_width=True)
    
    # График XP
    st.markdown('---')
    st.subheader('📊 Сравнение XP')
    
    fig_xp = px.bar(
        df_xp, x='Сотрудник', y='XP',
        color='Уровень',
        title='XP по сотрудникам',
        labels={'Сотрудник': 'Сотрудник', 'XP': 'Опыт'}
    )
    st.plotly_chart(fig_xp, use_container_width=True)

# ============================================
# СТРАНИЦА 5: АНАЛИТИКА
# ============================================
elif page == '📈 Аналитика':
    st.title('📈 Аналитика')
    
    # Собираем данные по всем месяцам
    all_data = []
    for month in MONTHS_DATA.keys():
        for emp in EMPLOYEES:
            hours = get_month_data(data, month, emp)
            if sum(hours) > 0:
                stats = calculate_stats(hours, MONTHS_DATA[month]['norm'])
                all_data.append({
                    'Месяц': month,
                    'Сотрудник': emp,
                    'Часы': stats['total'],
                    'Переработка': stats['overtime'],
                    'Эффективность': stats['efficiency'],
                })
    
    df_all = pd.DataFrame(all_data)
    
    if len(df_all) == 0:
        st.warning('⚠️ Нет данных. Введите часы на странице "Ввод часов".')
    else:
        # Динамика по месяцам
        st.subheader('📈 Динамика часов по месяцам')
        
        fig_trend = px.line(
            df_all, x='Месяц', y='Часы', color='Сотрудник',
            markers=True,
            title='Часы по месяцам',
            labels={'Месяц': 'Месяц', 'Часы': 'Часы', 'Сотрудник': 'Сотрудник'}
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Тепловая карта
        st.subheader(' Тепловая карта эффективности')
        
        pivot_eff = df_all.pivot_table(
            values='Эффективность',
            index='Сотрудник',
            columns='Месяц',
            aggfunc='mean'
        )
        
        fig_heat = px.imshow(
            pivot_eff,
            labels=dict(x="Месяц", y="Сотрудник", color="Эффективность %"),
            x=pivot_eff.columns,
            y=pivot_eff.index,
            color_continuous_scale='RdYlGn',
            title='Эффективность по месяцам (%)'
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Сравнение переработок
        st.subheader('🔥 Сравнение переработок')
        
        pivot_over = df_all.pivot_table(
            values='Переработка',
            index='Сотрудник',
            columns='Месяц',
            aggfunc='sum'
        )
        
        fig_over = px.bar(
            pivot_over,
            barmode='group',
            title='Переработки по месяцам',
            labels={'value': 'Переработка', 'Сотрудник': 'Сотрудник', 'Месяц': 'Месяц'}
        )
        st.plotly_chart(fig_over, use_container_width=True)
        
        # Сводная статистика
        st.subheader('📊 Сводная статистика')
        
        summary = df_all.groupby('Сотрудник').agg({
            'Часы': 'sum',
            'Переработка': 'sum',
            'Эффективность': 'mean'
        }).round(1)
        
        summary.columns = ['Всего часов', 'Всего переработок', 'Средняя эффективность %']
        summary = summary.sort_values('Всего часов', ascending=False)
        
        st.dataframe(summary, use_container_width=True)
        
        # Круговая диаграмма распределения часов
        st.subheader('🥧 Распределение часов между сотрудниками')
        
        fig_pie = px.pie(
            summary.reset_index(),
            values='Всего часов',
            names='Сотрудник',
            title='Доля часов каждого сотрудника'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
