# app.py
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Захватывать информационные сообщения
    event_level=logging.ERROR  # Отправлять в Sentry только ошибки
)
sentry_sdk.init(
    dsn=st.secrets["sentry_dsn"],
    integrations=[sentry_logging],
    traces_sample_rate=0.1
)
import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import logging

# Page config
st.set_page_config(page_title="Feature Roadmap Tool", layout="wide")

# Language switcher
lang = st.sidebar.selectbox("Language / Язык", ["EN", "RU"])
LABELS = {
    "EN": {
        "title": "🗺️ Feature Roadmap & Team Load",
        "event_name": "Event name",
        "event_type": "Event type",
        "release_date": "Release date",
        "add_event": "Add event",
        "days": "days",
        "events_list": "📅 Events list",
        "manage_events": "🛠️ Manage events",
        "delete": "Delete",
        "reset": "Reset",
        "move_left": "← -1 day",
        "move_right": "+1 day →",
        "download_gantt": "📸 Download Gantt (png)",
        "download_load": "📸 Download Load Chart (png)",
        "kpi_title": "📊 KPI Roadmap",
        "heatmap_title": "🌡️ Load Heatmap",
        "weekly_chart_title": "📆 Weekly Load Chart",
        "export_csv": "📂 Download KPI CSV",
        "select_disciplines": "Select disciplines to display",
        "save_project": "💾 Save Project",
        "load_project": "📂 Load Project",
        "project_saved": "Project saved",
        "project_loaded": "Project loaded",
        "search": "🔍 Search by name",
        "filter_types": "Filter by type",
        "no_data": "No data to display"
    },
    "RU": {
        "title": "🗺️ План фичей и загрузка команды",
        "event_name": "Название события",
        "event_type": "Тип события",
        "release_date": "Дата релиза",
        "add_event": "Добавить событие",
        "days": "дней",
        "events_list": "📅 Список событий",
        "manage_events": "🛠️ Управление событиями",
        "delete": "Удалить",
        "reset": "Сбросить",
        "move_left": "← -1 день",
        "move_right": "+1 день →",
        "download_gantt": "📸 Скачать Gantt (png)",
        "download_load": "📸 Скачать график загрузки (png)",
        "kpi_title": "📊 KPI Roadmap",
        "heatmap_title": "🌡️ Тепловая карта загрузки",
        "weekly_chart_title": "📆 Еженедельная загрузка",
        "export_csv": "📂 Скачать KPI CSV",
        "select_disciplines": "Выберите дисциплины для отображения",
        "save_project": "💾 Сохранить проект",
        "load_project": "📂 Загрузить проект",
        "project_saved": "Проект сохранён",
        "project_loaded": "Проект загружен",
        "search": "🔍 Поиск по названию",
        "filter_types": "Фильтр по типу",
        "no_data": "Нет данных для отображения"
    }
}
st.title(LABELS[lang]["title"])

# Holidays in Czechia 2025–2030
base_holidays = [(1,1),(4,18),(4,21),(5,1),(5,8),(7,5),(7,6),(9,28),(10,28),(11,17),(12,24),(12,25),(12,26)]
holidays_cz = [
    datetime(year, m, d)
    for year in range(2025, 2031)
    for (m, d) in base_holidays
]

# Default durations per feature type
default_durations_per_type = {
    "Repeat-Core (M)":    {"Concept":15, "Pre-prod":15,  "Production":30,  "Stabilization":30},
    "Repeat-Plus (L)":    {"Concept":15, "Pre-prod":30,  "Production":60,  "Stabilization":30},
    "Hybrid-Event (L)":   {"Concept":30, "Pre-prod":30,  "Production":90,  "Stabilization":30},
    "Meta-Boost (S-M)":   {"Concept":15, "Pre-prod":15,  "Production":30,  "Stabilization":30},
    "Prime-Event (XL)":   {"Concept":30, "Pre-prod":45,  "Production":150, "Stabilization":30}
}

# Resources per phase per feature type
resources_per_phase = {
    "Repeat-Core (M)": {
        "Concept":      {"GD":1,"SD":1,"UX":1,"GP/FE":1,"QA":1,"PM":1},
        "Pre-prod":     {"GD":1,"SD":1,"UX":1,"GP/FE":2,"QA":2,"PM":1},
        "Production":   {"GD":1,"SD":1,"UX":1,"GP/FE":3,"QA":3,"PM":1},
        "Stabilization":{"GD":1,"SD":1,"UX":1,"GP/FE":1,"QA":3,"PM":1}
    },
    "Repeat-Plus (L)": {
        "Concept":      {"GD":1,"SD":1,"UX":1,"GP/FE":1,"QA":1,"PM":1},
        "Pre-prod":     {"GD":1,"SD":1,"UX":2,"GP/FE":2,"QA":2,"PM":1},
        "Production":   {"GD":1,"SD":1,"UX":1,"GP/FE":3,"QA":3,"PM":1},
        "Stabilization":{"GD":1,"SD":1,"UX":1,"GP/FE":2,"QA":4,"PM":1}
    },
    "Hybrid-Event (L)": {
        "Concept":      {"GD":1,"SD":1,"UX":1,"GP/FE":1,"QA":1,"PM":1},
        "Pre-prod":     {"GD":1,"SD":1,"UX":2,"GP/FE":2,"QA":2,"PM":1},
        "Production":   {"GD":1,"SD":1,"UX":1,"GP/FE":3,"QA":3,"PM":1},
        "Stabilization":{"GD":1,"SD":1,"UX":1,"GP/FE":2,"QA":4,"PM":1}
    },
    "Meta-Boost (S-M)": {
        "Concept":      {"GD":1,"SD":1,"UX":1,"GP/FE":1,"QA":1,"PM":1},
        "Pre-prod":     {"GD":1,"SD":1,"UX":1,"GP/FE":2,"QA":2,"PM":1},
        "Production":   {"GD":1,"SD":1,"UX":1,"GP/FE":2,"QA":2,"PM":1},
        "Stabilization":{"GD":1,"SD":1,"UX":1,"GP/FE":1,"QA":3,"PM":1}
    },
    "Prime-Event (XL)": {
        "Concept":      {"GD":2,"SD":1,"UX":2,"GP/FE":1,"QA":1,"PM":1},
        "Pre-prod":     {"GD":2,"SD":1,"UX":2,"GP/FE":3,"QA":2,"PM":1},
        "Production":   {"GD":1,"SD":1,"UX":1,"GP/FE":5,"QA":4,"PM":1},
        "Stabilization":{"GD":1,"SD":1,"UX":1,"GP/FE":4,"QA":5,"PM":1}
    }
}

# Team capacity
team_capacity = {"GD":3, "SD":1, "UX":4, "GP/FE":6, "QA":7, "PM":1}

# Initialize session state
if 'events' not in st.session_state:
    st.session_state['events'] = []

# Save / Load project
col1, col2 = st.columns(2)
with col1:
    if st.download_button(LABELS[lang]["save_project"], json.dumps(st.session_state['events']), "roadmap.json"):
        st.success(LABELS[lang]["project_saved"])
with col2:
    uploaded = st.file_uploader(LABELS[lang]["load_project"], type="json")
    if uploaded:
        st.session_state['events'] = json.load(uploaded)
        st.success(LABELS[lang]["project_loaded"])

# Add Event form with editable durations
with st.form("add_event"):
    name = st.text_input(LABELS[lang]["event_name"])
    type_ = st.selectbox(LABELS[lang]["event_type"], list(default_durations_per_type.keys()))
    release_date = st.date_input(LABELS[lang]["release_date"], datetime.today())
    durations = {}
    for phase, default in default_durations_per_type[type_].items():
        durations[phase] = st.number_input(
            f"{phase} ({default} {LABELS[lang]['days']})",
            min_value=1, value=default, step=1, key=f"dur_{phase}"
        )
    submitted = st.form_submit_button(LABELS[lang]["add_event"])
    if submitted:
        st.session_state['events'].append({
            "name": name,
            "type": type_,
            "release": release_date.strftime("%Y-%m-%d"),
            "original_release": release_date.strftime("%Y-%m-%d"),
            "durations": durations
        })
        st.success(f"{name} {LABELS[lang]['add_event'].lower()}!")

# Filters
search_text = st.text_input(LABELS[lang]["search"])
filter_types = st.multiselect(LABELS[lang]["filter_types"], list(resources_per_phase.keys()))
filtered = [
    e for e in st.session_state['events']
    if search_text.lower() in e['name'].lower()
    and (not filter_types or e['type'] in filter_types)
]
st.subheader(LABELS[lang]["events_list"])
if filtered:
    st.write(filtered)
else:
    st.info(LABELS[lang]["no_data"])

# Manage events
st.subheader(LABELS[lang]["manage_events"])
for i, ev in enumerate(filtered):
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.write(f"**{ev['name']} ({ev['type']})**")
    with c2:
        if st.button(LABELS[lang]["move_left"], key=f"ml_{i}"):
            dt = datetime.strptime(ev['release'],"%Y-%m-%d") - timedelta(days=1)
            ev['release']=dt.strftime("%Y-%m-%d")
    with c3:
        if st.button(LABELS[lang]["move_right"], key=f"mr_{i}"):
            dt = datetime.strptime(ev['release'],"%Y-%m-%d") + timedelta(days=1)
            ev['release']=dt.strftime("%Y-%m-%d")
    with c4:
        if st.button(LABELS[lang]["reset"], key=f"rs_{i}"):
            ev['release']=ev.get('original_release',ev['release'])
    with c5:
        if st.button(LABELS[lang]["delete"], key=f"del_{i}"):
            st.session_state['events'].remove(ev)
            st.experimental_rerun()

# Helper: skip weekends & holidays
def prev_working_day(d):
    while d.weekday()>=5 or d in holidays_cz:
        d -= timedelta(days=1)
    return d

# Build Gantt & load data
gantt_data = []
resource_load = []
for ev in st.session_state['events']:
    end = datetime.strptime(ev['release'], "%Y-%m-%d")
    for phase in reversed(list(ev['durations'].keys())):
        dur = ev['durations'][phase]
        ph_end = end
        for _ in range(dur):
            ph_end = prev_working_day(ph_end - timedelta(days=1))
        ph_start = ph_end
        gantt_data.append({
            "Task": f"{ev['name']} - {phase}",
            "Start": ph_start,
            "Finish": end,
            "Resource": phase
        })
        cur = ph_start
        while cur < end:
            if cur.weekday()<5 and cur not in holidays_cz:
                entry = {"date": cur}
                entry.update(resources_per_phase[ev['type']][phase])
                resource_load.append(entry)
            cur += timedelta(days=1)
        end = ph_start

# Add holidays as Gantt tasks
for h in holidays_cz:
    gantt_data.append({"Task":"Holiday","Start":h,"Finish":h+timedelta(days=1),"Resource":"Holiday"})

# Gantt colors
colors = {
    "Concept":"rgb(200,200,255)","Pre-prod":"rgb(200,255,200)",
    "Production":"rgb(255,200,200)","Stabilization":"rgb(255,255,200)",
    "Holiday":"rgb(255,150,150)"
}

# Gantt chart
if gantt_data:
    df_gantt = pd.DataFrame(gantt_data)
    fig = ff.create_gantt(df_gantt, index_col="Resource", colors=colors,
                          show_colorbar=True, group_tasks=True)
    st.plotly_chart(fig)
    st.download_button(LABELS[lang]["download_gantt"], fig.to_image(format="png"), file_name="gantt.png")
else:
    st.warning(LABELS[lang]["no_data"])

# Daily load chart & CSV
if resource_load:
    df_load = pd.DataFrame(resource_load)
    df_day = df_load.groupby("date").sum().reset_index()
    fig2 = go.Figure()
    for role in team_capacity:
        fig2.add_trace(go.Scatter(x=df_day["date"], y=df_day[role], name=role))
        fig2.add_trace(go.Scatter(x=df_day["date"], y=[team_capacity[role]]*len(df_day),
                                  name=f"{role} cap", line=dict(dash="dash")))
    st.plotly_chart(fig2)
    st.download_button(LABELS[lang]["download_load"], fig2.to_image(format="png"), file_name="load.png")

    # KPI block
    st.subheader(LABELS[lang]["kpi_title"])
    kpi_start = df_gantt["Start"].min()
    kpi_end   = df_gantt["Finish"].max()
    df_kpi = df_day[(df_day["date"]>=kpi_start)&(df_day["date"]<=kpi_end)]
    total_mm = df_kpi.drop(columns="date").sum().sum()/30
    st.write(f"Total man-months: {total_mm:.1f}")
    for role in team_capacity:
        util = 100*df_kpi[role].sum()/(team_capacity[role]*len(df_kpi))
        st.write(f"{role}: {util:.1f}%")

    # Heatmap
    st.subheader(LABELS[lang]["heatmap_title"])
    sel = st.multiselect(LABELS[lang]["select_disciplines"], list(team_capacity.keys()), default=list(team_capacity.keys()))
    if sel:
        fig_h, ax = plt.subplots(figsize=(10,4))
        sns.heatmap(df_kpi.set_index("date")[sel].T, cmap="YlOrRd", ax=ax)
        st.pyplot(fig_h)

    # Weekly stacked chart
    st.subheader(LABELS[lang]["weekly_chart_title"])
    df_week = df_kpi.copy()
    df_week["week"] = df_week["date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_wg = df_week.groupby("week")[list(team_capacity.keys())].sum().reset_index()
    fig_w = go.Figure()
    for role in team_capacity:
        fig_w.add_trace(go.Bar(x=df_wg["week"], y=df_wg[role], name=role))
    fig_w.update_layout(barmode="stack")
    st.plotly_chart(fig_w)

    # Export weekly CSV
    csv = df_wg.to_csv(index=False).encode("utf-8")
    st.download_button(LABELS[lang]["export_csv"], csv, file_name="weekly_kpi.csv", mime="text/csv")
else:
    st.warning(LABELS[lang]["no_data"])
