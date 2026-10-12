from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="Мониторинг самолётов",
    page_icon="✈️",
    layout="wide",
)

@st.cache_data(ttl=60)
def load_dashboard_data(dbname, user, password, host, port):
    """Загружает данные из БД в режиме только для чтения."""
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

    try:
        conn.set_session(readonly=True, autocommit=True)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.icao24,
                    a.callsign,
                    ac.country_code AS registration_country,
                    a.latitude,
                    a.longitude,
                    a.velocity,
                    a.altitude,
                    a.on_ground
                FROM aircraft AS a
                LEFT JOIN aircraft_countries AS ac
                    ON a.country_id = ac.country_id
                ORDER BY a.icao24;
                """
            )
            aircraft_rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM flight_observations;")
            observation_count = cur.fetchone()[0]

        columns = [
            "icao24",
            "callsign",
            "registration_country",
            "latitude",
            "longitude",
            "velocity",
            "altitude",
            "on_ground",
        ]

        aircraft = pd.DataFrame(aircraft_rows, columns=columns)
        return aircraft, observation_count
    finally:
        conn.close()

st.title("✈️ Мониторинг самолётов")
st.caption("Просмотр данных из PostgreSQL — без изменения базы.")

required = ("DB_NAME", "DB_USER", "DB_PASSWORD")
missing = [name for name in required if not os.getenv(name)]

if missing:
    st.error(
        "В файле .env не заданы обязательные настройки: "
        + ", ".join(missing)
    )
    st.stop()

db_config = (
    os.getenv("DB_NAME"),
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"),
    os.getenv("DB_HOST", "localhost"),
    int(os.getenv("DB_PORT", "5432")),
)

if st.button("Обновить данные на странице"):
    load_dashboard_data.clear()

try:
    aircraft, observation_count = load_dashboard_data(*db_config)
except psycopg2.Error as error:
    st.error(f"Не удалось подключиться к базе данных: {error}")
    st.stop()

if aircraft.empty:
    st.info("В таблице aircraft пока нет самолётов.")
    st.stop()

aircraft["altitude"] = pd.to_numeric(aircraft["altitude"], errors="coerce")
aircraft["velocity"] = pd.to_numeric(aircraft["velocity"], errors="coerce")

countries = sorted(
    aircraft["registration_country"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_countries = st.sidebar.multiselect(
    "Страна регистрации",
    options=countries,
    help="Если ничего не выбрано, отображаются все страны.",
)

filtered = aircraft.copy()

if selected_countries:
    filtered = filtered[
        filtered["registration_country"].isin(selected_countries)
    ]

if filtered.empty:
    st.warning("Для выбранных фильтров самолёты не найдены.")
    st.stop()

average_altitude = filtered["altitude"].mean()
above_average_count = (
    int(filtered["altitude"].gt(average_altitude).sum())
    if pd.notna(average_altitude)
    else 0
)

metric_columns = st.columns(4)
metric_columns[0].metric("Самолётов", f"{len(filtered):,}".replace(",", " "))
metric_columns[1].metric(
    "Средняя высота",
    f"{average_altitude:,.0f} м".replace(",", " ")
    if pd.notna(average_altitude)
    else "Нет данных",
)
metric_columns[2].metric(
    "Выше средней высоты",
    f"{above_average_count:,}".replace(",", " "),
)
metric_columns[3].metric(
    "Наблюдений в базе",
    f"{observation_count:,}".replace(",", " "),
)

st.subheader("Количество самолётов по стране регистрации")

country_counts = (
    filtered.assign(
        registration_country=filtered["registration_country"].fillna("Не указана")
    )
    .groupby("registration_country")
    .size()
    .rename("Самолётов")
    .reset_index()
    .sort_values("Самолётов", ascending=False)
)

st.bar_chart(
    country_counts,
    x="registration_country",
    y="Самолётов",
)

altitudes = filtered["altitude"].dropna()

if not altitudes.empty:
    st.subheader("Распределение самолётов по высоте")

    altitude_bins = pd.cut(altitudes, bins=10)
    altitude_counts = (
        altitude_bins.value_counts()
        .sort_index()
        .rename("Самолётов")
        .reset_index()
    )
    altitude_counts.columns = ["Диапазон высоты", "Самолётов"]
    altitude_counts["Диапазон высоты"] = (
        altitude_counts["Диапазон высоты"].astype(str)
    )

    st.bar_chart(
        altitude_counts,
        x="Диапазон высоты",
        y="Самолётов",
    )

st.subheader("Самолёты")

display_data = filtered.rename(
    columns={
        "icao24": "ICAO24",
        "callsign": "Позывной",
        "registration_country": "Страна регистрации",
        "latitude": "Широта",
        "longitude": "Долгота",
        "velocity": "Скорость",
        "altitude": "Высота",
        "on_ground": "На земле",
    }
)

st.dataframe(
    display_data,
    hide_index=True,
    width="stretch",
)

# poetry run streamlit run app.py
