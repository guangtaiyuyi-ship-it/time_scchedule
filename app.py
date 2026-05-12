import streamlit as st
import pandas as pd
from datetime import time, datetime, date, timedelta
import os
import plotly.express as px

# --- 1. 画面のタイトル ---
st.set_page_config(page_title="タイムスケジュール帳", layout="wide")
st.title("私のタイムスケジュール帳")

# --- 2. データの保存先 ---
csv_file_path = "schedule.csv"
template_csv_path = "template_schedule.csv"


# --- 3. データを読み込む仕組み ---
def load_data():
    if os.path.exists(csv_file_path):
        return pd.read_csv(csv_file_path)
    else:
        return pd.DataFrame(columns=["日付", "タスク", "開始時間", "終了時間"])


def load_template_data():
    if os.path.exists(template_csv_path):
        return pd.read_csv(template_csv_path)
    else:
        return pd.DataFrame(columns=["曜日", "タスク", "開始時間", "終了時間"])


df_schedule = load_data()
df_template = load_template_data()

# ==========================================
# --- 左側のサイドバー（テンプレート設定・削除） ---
# ==========================================
st.sidebar.header("⚙️ 曜日ごとの基本テンプレート")

st.sidebar.subheader("➕ 新規登録")
temp_day = st.sidebar.selectbox(
    "曜日を選択", ["月", "火", "水", "木", "金", "土", "日"]
)
temp_task = st.sidebar.text_input("タスク名", "朝食・準備", key="t_task")
temp_start = st.sidebar.time_input("開始時間", time(7, 0), key="t_start")
temp_end = st.sidebar.time_input("終了時間", time(8, 0), key="t_end")

if st.sidebar.button("テンプレートに登録する"):
    new_temp = pd.DataFrame(
        {
            "曜日": [temp_day],
            "タスク": [temp_task],
            "開始時間": [temp_start.strftime("%H:%M")],
            "終了時間": [temp_end.strftime("%H:%M")],
        }
    )

    df_template = pd.concat([df_template, new_temp], ignore_index=True)
    df_template.to_csv(template_csv_path, index=False)
    st.sidebar.success(f"毎週{temp_day}曜日に「{temp_task}」を登録しました！")
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("🗑️ 登録済みテンプレートの管理")

if not df_template.empty:
    for index, row in df_template.iterrows():
        st.sidebar.write(
            f"**{row['曜日']}曜** {row['開始時間']}~{row['終了時間']} : {row['タスク']}"
        )
        if st.sidebar.button("削除", key=f"del_temp_{index}"):
            df_template = df_template.drop(index)
            df_template.to_csv(template_csv_path, index=False)
            st.rerun()
else:
    st.sidebar.write("現在登録されているテンプレートはありません。")


# ==========================================
# --- グラフを作る専用の機械（関数） ---
# ==========================================
def create_pie_chart(day_schedule, font_size=14):
    if day_schedule.empty:
        return None

    day_schedule = day_schedule.sort_values(by="開始時間")
    pie_labels_clean = []
    pie_labels_unique = []
    pie_values = []
    display_texts = []

    current_dt = datetime.strptime("00:00", "%H:%M")
    counter = 0

    for index, row in day_schedule.iterrows():
        start_dt = datetime.strptime(str(row["開始時間"]), "%H:%M")
        end_dt = datetime.strptime(str(row["終了時間"]), "%H:%M")

        if start_dt > current_dt:
            free_hours = (start_dt - current_dt).seconds / 3600
            pie_labels_clean.append("空き時間")
            pie_labels_unique.append(f"空き時間_{counter}")
            pie_values.append(free_hours)
            display_texts.append("")
            counter += 1

        actual_start = max(start_dt, current_dt)
        if end_dt > actual_start:
            task_hours = (end_dt - actual_start).seconds / 3600
            pie_labels_clean.append(row["タスク"])
            pie_labels_unique.append(f"{row['タスク']}_{counter}")
            pie_values.append(task_hours)

            time_range_str = (
                f"<b>{actual_start.strftime('%H:%M')}~{end_dt.strftime('%H:%M')}</b>"
            )
            display_texts.append(f"{row['タスク']}<br>{time_range_str}")

            current_dt = end_dt
            counter += 1

    total_hours = sum(pie_values)
    if total_hours < 24:
        pie_labels_clean.append("空き時間")
        pie_labels_unique.append(f"空き時間_{counter}")
        pie_values.append(24 - total_hours)
        display_texts.append("")

    chart_df = pd.DataFrame(
        {
            "一意な名前": pie_labels_unique,
            "表示名": pie_labels_clean,
            "時間（時間）": pie_values,
            "グラフ用テキスト": display_texts,
        }
    )

    colors = []
    color_palette = px.colors.qualitative.Set2
    task_color_map = {}
    color_idx = 0

    for name in pie_labels_clean:
        if name == "空き時間":
            colors.append("#F4F4F4")
        else:
            if name not in task_color_map:
                task_color_map[name] = color_palette[color_idx % len(color_palette)]
                color_idx += 1
            colors.append(task_color_map[name])

    fig = px.pie(
        chart_df,
        values="時間（時間）",
        names="一意な名前",
        custom_data=["グラフ用テキスト"],
        hole=0.4,
    )

    fig.update_traces(
        sort=False,
        direction="clockwise",
        rotation=0,
        texttemplate="%{customdata[0]}",
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textposition="inside",
        textfont=dict(size=font_size),
    )

    fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    return fig


# ==========================================
# --- 4. 一週間の日付を計算する ---
# ==========================================
st.header("📅 表示する週の選択")
base_date = st.date_input("基準となる日付を選んでください", date.today())
start_of_week = base_date - timedelta(days=base_date.weekday())
week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
week_days_str = ["月", "火", "水", "木", "金", "土", "日"]


# ==========================================
# --- データの合体ロジック ---
# ==========================================
def get_combined_schedule(target_date_str, target_weekday_str):
    if not df_template.empty and "曜日" in df_template.columns:
        day_temp = df_template[df_template["曜日"] == target_weekday_str].copy()
    else:
        day_temp = pd.DataFrame(columns=["タスク", "開始時間", "終了時間"])

    if not df_schedule.empty and "日付" in df_schedule.columns:
        day_spec = df_schedule[df_schedule["日付"] == target_date_str].copy()
    else:
        day_spec = pd.DataFrame(columns=["タスク", "開始時間", "終了時間"])

    combined = pd.concat([day_temp, day_spec], ignore_index=True)
    return combined


# ==========================================
# --- 5. 一週間のダッシュボード ---
# ==========================================
st.header("📊 今週のスケジュール全体図")

cols_top = st.columns(4)
cols_bottom = st.columns(4)

for i in range(7):
    current_date_str = week_dates[i].strftime("%Y-%m-%d")
    current_weekday_str = week_days_str[i]

    day_schedule = get_combined_schedule(current_date_str, current_weekday_str)

    if i < 4:
        target_col = cols_top[i]
    else:
        target_col = cols_bottom[i - 4]

    with target_col:
        st.markdown(f"**{current_weekday_str} ({week_dates[i].strftime('%m/%d')})**")
        fig = create_pie_chart(day_schedule, font_size=12)

        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"dash_chart_{i}")
        else:
            st.write("予定なし")

st.write("---")

# ==========================================
# --- 6. 曜日ごとの編集タブ ---
# ==========================================
st.header("✏️ 日ごとの個別予定編集")
st.write("※ テンプレート以外の、この日だけの特別な予定を追加・削除します。")

tabs = st.tabs(
    [f"{week_days_str[i]} ({week_dates[i].strftime('%m/%d')})" for i in range(7)]
)

for i in range(7):
    current_date_str = week_dates[i].strftime("%Y-%m-%d")
    current_weekday_str = week_days_str[i]

    with tabs[i]:
        # --- A. 個別予定の追加 ---
        st.subheader(f"📝 {current_date_str} の予定追加")

        task_name = st.text_input("タスク名", "打ち合わせ", key=f"task_{i}")
        start_time = st.time_input("開始時間", time(13, 0), key=f"start_{i}")
        end_time = st.time_input("終了時間", time(14, 0), key=f"end_{i}")

        if st.button("個別の予定を追加する", key=f"btn_{i}"):
            new_data = pd.DataFrame(
                {
                    "日付": [current_date_str],
                    "タスク": [task_name],
                    "開始時間": [start_time.strftime("%H:%M")],
                    "終了時間": [end_time.strftime("%H:%M")],
                }
            )
            df_schedule = pd.concat([df_schedule, new_data], ignore_index=True)
            df_schedule.to_csv(csv_file_path, index=False)
            st.success(f"{current_date_str}に予定を追加しました！")
            st.rerun()

        st.markdown("---")

        # ==========================================
        # --- B. 個別予定の管理（削除） ---
        # ==========================================
        st.subheader("🗑️ この日の個別予定の管理")

        if not df_schedule.empty and "日付" in df_schedule.columns:
            today_tasks = df_schedule[df_schedule["日付"] == current_date_str]

            if not today_tasks.empty:
                for index, row in today_tasks.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(
                            f"**{row['開始時間']}~{row['終了時間']}** : {row['タスク']}"
                        )
                    with col2:
                        if st.button("削除", key=f"del_task_{index}_{i}"):
                            # 【修正点】global宣言を削除し、そのままデータを切り捨てて保存します
                            df_schedule = df_schedule.drop(index)
                            df_schedule.to_csv(csv_file_path, index=False)
                            st.rerun()
            else:
                st.write("この日に追加された個別予定はありません。")
        else:
            st.write("この日に追加された個別予定はありません。")

        st.markdown("---")

        # --- C. 大きな円グラフの表示 ---
        day_schedule = get_combined_schedule(current_date_str, current_weekday_str)

        st.subheader("📊 この日の詳細グラフ（基本＋個別）")
        big_fig = create_pie_chart(day_schedule, font_size=18)
        if big_fig:
            st.plotly_chart(big_fig, use_container_width=True, key=f"tab_chart_{i}")
        else:
            st.write("予定を追加するとグラフが表示されます。")
