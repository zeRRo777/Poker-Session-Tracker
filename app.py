import streamlit as st
import pandas as pd
import plotly.express as px
import database as db
import logic
from datetime import date, timedelta
import time

# Настройка страницы
st.set_page_config(page_title="Poker Session Tracker", layout="wide", page_icon="♠️")

st.markdown(
    """
    <style>
    .stAppDeployButton, #MainMenu {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Инициализация БД
db.init_db()

# --- SIDEBAR (Фильтры) ---
st.sidebar.title("♣️ Фильтры")

# Фильтр дат
filter_period = st.sidebar.selectbox(
    "Период",
    ["Все время", "Последние 30 дней", "Текущий год", "Выбрать даты"]
)

start_date = None
end_date = None

if filter_period == "Последние 30 дней":
    start_date = date.today() - timedelta(days=30)
    end_date = date.today()
elif filter_period == "Текущий год":
    start_date = date(date.today().year, 1, 1)
    end_date = date.today()
elif filter_period == "Выбрать даты":
    d = st.sidebar.date_input("Диапазон", [date.today() - timedelta(days=7), date.today()])
    if isinstance(d, tuple) and len(d) == 2:
        start_date, end_date = d
    elif isinstance(d, tuple) and len(d) == 1:
        start_date = d[0]
        end_date = d[0]
    else:
        start_date = date.today()
        end_date = date.today()

# Загрузка справочников для фильтров
rooms_df = db.get_rooms()
types_df = db.get_game_types()

# Фильтр по руму
room_options = ["All"] + rooms_df['name'].tolist()
selected_room = st.sidebar.selectbox("Покер-рум", room_options)

# Фильтр по типу игры
type_options = ["All"] + types_df['name'].tolist()
selected_type = st.sidebar.selectbox("Тип игры", type_options)

# --- ЗАГРУЗКА ДАННЫХ ---
df = db.get_sessions_df()

# Применение фильтров
if start_date and end_date:
    df['date_only'] = df['date'].dt.date
    df = df[(df['date_only'] >= start_date) & (df['date_only'] <= end_date)]
    df = df.drop(columns=['date_only'])

if selected_room != "All":
    df = df[df['room'] == selected_room]

if selected_type != "All":
    df = df[df['game_type'] == selected_type]

# --- ГЛАВНАЯ НАВИГАЦИЯ ---
tab1, tab2, tab3 = st.tabs(["📊 Аналитика", "📝 Журнал", "⚙️ Настройки"])

# ==========================
# PAGE 1: DASHBOARD
# ==========================
with tab1:
    st.title("Аналитика сессий")

    # Блок 1: KPI
    total_profit, hourly, count, winrate = logic.calculate_kpi(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Profit", f"${total_profit:,.2f}", delta_color="normal")
    col2.metric("Hourly Rate", f"${hourly:.2f}/hr")
    col3.metric("Total Sessions", count)
    col4.metric("Win Rate", f"{winrate:.1f}%")

    st.divider()

    # Блок 2: Графики
    if not df.empty:
        # Cumulative Profit
        df_sorted = df.sort_values(by='date')
        df_sorted['cumulative_profit'] = df_sorted['profit'].cumsum()

        fig_cum = px.line(df_sorted, x='date', y='cumulative_profit',
                          title="График накопленной прибыли (Cumulative Profit)",
                          markers=True)
        st.plotly_chart(fig_cum, use_container_width=True)

        # Profit by Month
        df_sorted['month_year'] = df_sorted['date'].dt.to_period('M').astype(str)
        monthly_profit = df_sorted.groupby('month_year')['profit'].sum().reset_index()

        fig_bar = px.bar(monthly_profit, x='month_year', y='profit',
                         title="Прибыль по месяцам",
                         color='profit',
                         color_continuous_scale=['red', 'green'])
        st.plotly_chart(fig_bar, use_container_width=True)

        # Блок 3
        c_left, c_right = st.columns(2)

        # Profit by Rooms
        with c_left:
            st.subheader("Profit by Room")
            room_profit = df.groupby('room')['profit'].sum().reset_index()
            fig_room = px.bar(
                room_profit,
                x='room',
                y='profit',
                color='profit',
                color_continuous_scale=['red', 'green', 'green'],
                text_auto='.2s'
            )
            fig_room.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_room, use_container_width=True)

        # Profit by Game Types
        with c_right:
            st.subheader("Profit by Game Type")
            type_profit = df.groupby('game_type')['profit'].sum().reset_index()
            fig_type = px.bar(type_profit, x='game_type', y='profit', color='profit')
            st.plotly_chart(fig_type, use_container_width=True)

        # Блок 4: Рекорды и доп. метрики
        st.divider()
        st.subheader("Рекорды и Статистика")

        recs = logic.get_records(df)
        streak_win, streak_loss = logic.calculate_streaks(df)
        roi = logic.get_roi(df)

        r1, r2, r3, r4, r5 = st.columns(5)
        if recs:
            r1.metric("Best Win", f"${recs['best_win'][0]:.2f}", recs['best_win'][1])
            r2.metric("Worst Loss", f"${recs['worst_loss'][0]:.2f}", recs['worst_loss'][1])
        else:
            r1.metric("Best Win", "-")
            r2.metric("Worst Loss", "-")

        r3.metric("Longest Win Streak", f"{streak_win} sessions")
        r4.metric("Longest Loss Streak", f"{streak_loss} sessions")
        r5.metric("Total ROI", f"{roi:.2f}%")

    else:
        st.info("Нет данных для отображения за выбранный период.")


# ==========================
# PAGE 2: LOG (Журнал)
# ==========================

with tab2:
    st.header("Журнал сессий")

    # Добавление сессии
    with st.expander("➕ Добавить новую сессию", expanded=True):
        with st.form("add_session_form", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:
                input_date = st.date_input("Дата", date.today())
                input_duration = st.number_input("Длительность (мин)", min_value=1, value=60, step=60)

            with col_f2:
                if not rooms_df.empty:
                    room_map = dict(zip(rooms_df['name'], rooms_df['id']))
                    input_room = st.selectbox("Рум", list(room_map.keys()))
                else:
                    input_room = None
                    st.warning("Сначала добавьте покер-румы в настройках")

                if not types_df.empty:
                    type_map = dict(zip(types_df['name'], types_df['id']))
                    input_type = st.selectbox("Тип игры", list(type_map.keys()))
                else:
                    input_type = None
                    st.warning("Сначала добавьте типы игр в настройках")

            with col_f3:
                input_buyin = st.number_input("Buy-in ($)", min_value=0.0, step=1.0)
                input_cashout = st.number_input("Cash-out ($)", min_value=0.0, step=1.0)

            input_comment = st.text_area("Комментарий")

            submitted = st.form_submit_button("Сохранить сессию")

            if submitted:
                if input_room and input_type:
                    db.add_session(
                        input_date,
                        room_map[input_room],
                        type_map[input_type],
                        input_buyin,
                        input_cashout,
                        input_duration,
                        input_comment
                    )
                    profit = input_cashout - input_buyin
                    if profit > 0:
                        st.success(f"Сессия добавлена! Профит: ${profit:.2f}")
                    elif -1 < profit <= 0:
                        st.warning(f"Сессия добавлена! Профит: ${profit:.2f}")
                    else:
                        st.error(f"Сессия добавлена! Профит: ${profit:.2f}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Пожалуйста, убедитесь, что Румы и Типы игр созданы в настройках.")

    st.divider()

    # Редактирование / Просмотр сессии
    st.subheader("История")

    edit_df = df[
        ['id', 'date', 'room', 'game_type', 'buy_in', 'cash_out', 'profit', 'duration_minutes', 'comments']].copy()

    edited_data = st.data_editor(
        edit_df,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "profit": st.column_config.NumberColumn("Profit", disabled=True),
            "room": st.column_config.TextColumn("Room", disabled=True),
            "game_type": st.column_config.TextColumn("Game", disabled=True),
            "buy_in": st.column_config.NumberColumn("Buy-in", format="$%.2f"),
            "cash_out": st.column_config.NumberColumn("Cash-out", format="$%.2f"),
        },
        num_rows="dynamic",
        key="session_editor",
        use_container_width=True
    )

    if st.button("Применить изменения (Удалить / Изменить)"):
        changes = st.session_state["session_editor"]

        has_changes = False

        if changes["deleted_rows"]:
            for index in changes["deleted_rows"]:
                idx = int(index)
                if idx < len(edit_df):
                    session_id_to_delete = edit_df.iloc[idx]['id']
                    db.delete_session(int(session_id_to_delete))
                    st.toast(f"🗑️ Сессия {session_id_to_delete} удалена.")
                    has_changes = True

        if changes["edited_rows"]:
            for index_str, updates in changes["edited_rows"].items():
                try:
                    idx = int(index_str)

                    if idx < len(edit_df):
                        original_row = edit_df.iloc[idx]
                        session_id = int(original_row['id'])
                        new_date = updates.get("date", original_row["date"])
                        if hasattr(new_date, 'strftime'):
                            new_date = new_date.strftime('%Y-%m-%d')
                        def safe_float(val):
                            return float(val) if val is not None else 0.0

                        def safe_int(val):
                            return int(val) if val is not None else 0

                        val_buyin = updates.get("buy_in", original_row["buy_in"])
                        new_buyin = safe_float(val_buyin)

                        val_cashout = updates.get("cash_out", original_row["cash_out"])
                        new_cashout = safe_float(val_cashout)

                        val_dur = updates.get("duration_minutes", original_row["duration_minutes"])
                        new_duration = safe_int(val_dur)

                        new_comments = updates.get("comments", original_row["comments"])
                        if new_comments is None: new_comments = ""

                        db.update_session(session_id, new_date, new_buyin, new_cashout, new_duration, new_comments)
                        st.toast(f"✏️ Сессия {session_id} обновлена.")
                        has_changes = True
                except Exception as e:
                    st.error(f"Ошибка при обновлении строки {index_str}: {e}")

        if has_changes:
            st.success("Изменения успешно применены!")
            time.sleep(1.5)
            st.rerun()
        else:
            st.info("Нет изменений для сохранения.")


# ==========================
# PAGE 3: SETTINGS
# ==========================

with tab3:
    st.header("Настройки справочников")
    st.info("💡 Вы можете редактировать названия прямо в таблице. Нажмите 'Сохранить изменения' после правки.")

    col_s1, col_s2 = st.columns(2)

    # ROOMS
    with col_s1:
        st.subheader("Покер-румы")

        # Add Room
        with st.form("add_room_form", clear_on_submit=True):
            new_room = st.text_input("Название рума")
            if st.form_submit_button("Добавить рум"):
                if new_room:
                    db.add_room(new_room)
                    st.success(f"Рум {new_room} добавлен")
                    st.rerun()
        # Update Room
        rooms_df = db.get_rooms()
        edited_rooms = st.data_editor(
            rooms_df,
            column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Название"),
            "deleted_at": None
            },
            key="rooms_editor",
            num_rows="fixed",
            hide_index=True,
            use_container_width=True
        )

        col_btn1, col_btn2 = st.columns(2)

        if col_btn1.button("Сохранить названия румов"):
            changes = st.session_state.get("rooms_editor")

            if not changes or not changes.get("edited_rows"):
                st.warning("Нет изменений для сохранения.")
            else:
                count_updated = 0
                for index_str, updates in changes["edited_rows"].items():
                    idx = int(index_str)
                    if idx < len(rooms_df):
                        target_row = rooms_df.iloc[idx]
                        room_id = int(target_row['id'])
                        new_name = updates.get('name')

                        if new_name:
                            db.update_room(room_id, new_name)
                            count_updated += 1
                if count_updated > 0:
                    st.success(f"Обновлено записей: {count_updated}")
                    time.sleep(1)
                    st.rerun()

        #DELETE POKER ROOM
        st.divider()
        room_to_delete = st.selectbox("Удалить рум", ["Выберите..."] + rooms_df['name'].tolist())
        if st.button("Удалить выбранный рум"):
            if room_to_delete != "Выберите...":
                r_id = rooms_df[rooms_df['name'] == room_to_delete].iloc[0]['id']
                db.soft_delete_room(int(r_id))
                st.warning(f"Рум {room_to_delete} удален.")
                st.rerun()

    # GAME TYPES
    with col_s2:
        st.subheader("Типы игр")

        #ADD GAME TYPES
        with st.form("add_type_form", clear_on_submit=True):
            new_type = st.text_input("Название нового типа")
            if st.form_submit_button("Добавить"):
                if new_type:
                    db.add_game_type(new_type)
                    st.success(f"Тип {new_type} добавлен")
                    st.rerun()

        #UPDATE GAME TYPES
        types_df = db.get_game_types()
        edited_types = st.data_editor(
            types_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Название"),
                "deleted_at": None
            },
            key="types_editor",
            num_rows="fixed",
            hide_index=True,
            use_container_width=True
        )

        col_btn3, col_btn4 = st.columns(2)

        if col_btn3.button("Сохранить названия типов"):
            changes = st.session_state.get("types_editor")
            if not changes or not changes.get("edited_rows"):
                st.warning("Нет изменений для сохранения.")
            else:
                count_updated = 0

                for index_str, updates in changes["edited_rows"].items():
                    idx = int(index_str)
                    if idx < len(types_df):
                        target_row = types_df.iloc[idx]
                        type_id = int(target_row['id'])
                        new_name = updates.get('name')
                        if new_name:
                            db.update_game_type(type_id, new_name)
                            count_updated += 1
                if count_updated > 0:
                    st.success(f"Обновлено записей: {count_updated}")
                    time.sleep(1)
                    st.rerun()

        # DELETE GAME TYPE
        st.divider()
        type_to_delete = st.selectbox("Удалить тип", ["Выберите..."] + types_df['name'].tolist())
        if st.button("Удалить выбранный тип"):
            if type_to_delete != "Выберите...":
                t_id = types_df[types_df['name'] == type_to_delete].iloc[0]['id']
                db.soft_delete_game_type(int(t_id))
                st.warning(f"Тип {type_to_delete} удален.")
                st.rerun()



