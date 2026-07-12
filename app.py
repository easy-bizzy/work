import streamlit as st
import pandas as pd

# ============================================
# НАСТРОЙКИ
# ============================================
st.set_page_config(page_title="Учёт времени", page_icon="🏆", layout="wide")

EMPLOYEES = ['Виталя', 'Василий', 'Александр П', 'Александр О', 'Игорь', 'Стас']
MONTHS = ['ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']
MONTHS_DATA = {
    'ИЮЛЬ': 184, 'АВГУСТ': 168, 'СЕНТЯБРЬ': 176, 
    'ОКТЯБРЬ': 176, 'НОЯБРЬ': 160, 'ДЕКАБРЬ': 184
}

# ============================================
# БЕЗОПАСНОЕ ХРАНЕНИЕ ДАННЫХ ДЛЯ ОБЛАКА
# ============================================
@st.cache_resource
def get_data():
    """Создает структуру данных в памяти (работает в облаке)"""
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
page = st.sidebar.radio('Меню', ['📊 Дашборд', '️ Ввод часов', '🏆 Рейтинг'])
month = st.sidebar.selectbox('Месяц', MONTHS)
norm = MONTHS_DATA[month]

# ============================================
# СТРАНИЦА 1: ДАШБОРД
# ============================================
if page == '📊 Дашборд':
    st.title(f' Дашборд — {month}')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency = calc_stats(hours, norm)
        stats_list.append({'Сотрудник': emp, 'Часы': total, 'Переработка': overtime, 'Эффективность': efficiency})
    
    df = pd.DataFrame(stats_list)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric('⏱ Всего часов', f"{df['Часы'].sum():.1f}")
    with col2: st.metric(' Переработка', f"{df['Переработка'].sum():.1f} ч")
    with col3: st.metric('📈 Ср. эффективность', f"{df['Эффективность'].mean():.0f}%")
    
    st.markdown('---')
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Часы')
        st.bar_chart(df.set_index('Сотрудник')['Часы'])
    with col2:
        st.subheader('Переработка')
        st.bar_chart(df.set_index('Сотрудник')['Переработка'])
    
    st.markdown('---')
    st.dataframe(df, use_container_width=True)

# ============================================
# СТРАНИЦА 2: ВВОД ЧАСОВ
# ============================================
elif page == '✏️ Ввод часов':
    st.title(f'✏️ Ввод часов — {month}')
    emp = st.selectbox('Сотрудник', EMPLOYEES)
    
    hours = get_hours(month, emp)
    st.subheader(f'Введи часы для: {emp}')
    
    new_hours = []
    # Делаем ввод по неделям, чтобы не было длинной простыни
    for week in range(5):
        st.markdown(f"**Неделя {week + 1}**")
        cols = st.columns(7)
        for i in range(7):
            day = week * 7 + i + 1
            if day > 31: break
            val = cols[i].number_input(f'День {day}', min_value=0.0, max_value=24.0, value=float(hours[day-1]), step=0.5, key=f'd{day}')
            new_hours.append(val)
        # Дополняем до 31 если нужно
        if len(new_hours) < 31 and week == 4:
            new_hours.extend([0.0] * (31 - len(new_hours)))

    if st.button('💾 Сохранить', type='primary', use_container_width=True):
        save_hours(month, emp, new_hours[:31])
        st.success('✅ Сохранено! Обнови страницу.')
        st.rerun()
    
    total, overtime, efficiency = calc_stats(new_hours[:31], norm)
    st.markdown('---')
    col1, col2, col3 = st.columns(3)
    with col1: st.metric('Всего', f'{total:.1f}')
    with col2: st.metric('Переработка', f'{overtime:.1f}')
    with col3: st.metric('Эффективность', f'{efficiency:.0f}%')

# ============================================
# СТРАНИЦА 3: РЕЙТИНГ
# ============================================
elif page == '🏆 Рейтинг':
    st.title(f'🏆 Рейтинг — {month}')
    
    stats_list = []
    for emp in EMPLOYEES:
        hours = get_hours(month, emp)
        total, overtime, efficiency = calc_stats(hours, norm)
        stats_list.append({'Сотрудник': emp, 'Часы': total, 'Переработка': overtime})
    
    df = pd.DataFrame(stats_list).sort_values('Часы', ascending=False).reset_index(drop=True)
    
    if len(df) >= 3:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div style="background:#C0C0C0; padding:20px; border-radius:10px; text-align:center;"><h2>🥈</h2><h3>{df.iloc[1]["Сотрудник"]}</h3><p>{df.iloc[1]["Часы"]:.1f} ч</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="background:#FFD700; padding:30px; border-radius:10px; text-align:center; border:3px solid gold;"><h1>🥇</h1><h2>{df.iloc[0]["Сотрудник"]}</h2><p style="font-size:24px;"><b>{df.iloc[0]["Часы"]:.1f} ч</b></p><p style="color:darkblue;"><b>ЕБАТЬ ТЫ МОЛОДЕЦ!</b></p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div style="background:#CD7F32; padding:20px; border-radius:10px; text-align:center;"><h2>🥉</h2><h3>{df.iloc[2]["Сотрудник"]}</h3><p>{df.iloc[2]["Часы"]:.1f} ч</p></div>', unsafe_allow_html=True)
    
    st.markdown('---')
    st.dataframe(df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="background:#FFD700; padding:20px; border-radius:10px;"><h2>🏆 ГРАМОТА</h2><h3 style="color:gold;">ЕБАТЬ ТЫ МОЛОДЕЦ</h3><p><b>{df.iloc[0]["Сотрудник"]}</b></p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div style="background:#8B4513; padding:20px; border-radius:10px;"><h2>📜 АНТИНАГРАДА</h2><h3 style="color:#D2B48C;">ЛОХ</h3><p><b>{df.iloc[-1]["Сотрудник"]}</b></p></div>', unsafe_allow_html=True)
