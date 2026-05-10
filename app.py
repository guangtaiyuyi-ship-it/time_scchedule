import streamlit as st
import pandas as pd
from datetime import time, datetime, date
import os
import plotly.express as px

# --- 1. 画面のタイトル ---
st.title("私のタイムスケジュール帳")

# --- 2. データの保存先 ---
csv_file_path = "schedule.csv"


# --- 3. データを読み込む仕組み ---
def load_data():
    if os.path.exists(csv_file_path):
        return pd.read_csv(csv_file_path)
    else:
        return pd.DataFrame(columns=["日付", "タスク", "開始時間", "終了時間"])


df_schedule = load_data()

# ==========================================
# --- 4. 表示する日付の選択（フィルター） ---
# ==========================================
st.header("📅 表示する日付の選択")
view_date = st.date_input("確認したい日付を選んでください", date.today())
view_date_str = view_date.strftime("%Y-%m-%d")

if not df_schedule.empty and "日付" in df_schedule.columns:
    df_schedule["日付"] = df_schedule["日付"].astype(str)
    day_schedule = df_schedule[df_schedule["日付"] == view_date_str].copy()
else:
    day_schedule = pd.DataFrame(columns=["日付", "タスク", "開始時間", "終了時間"])

# ==========================================
# --- 5. スケジュールの入力欄 ---
# ==========================================
st.header("📝 予定の追加")

add_date = st.date_input("追加する日付", view_date)
task_name = st.text_input("タスク名", "プログラミング学習")
start_time = st.time_input("開始時間", time(9, 0))
end_time = st.time_input("終了時間", time(10, 0))

if st.button("スケジュールに追加する"):
    new_data = pd.DataFrame(
        {
            "日付": [add_date.strftime("%Y-%m-%d")],
            "タスク": [task_name],
            "開始時間": [start_time.strftime("%H:%M")],
            "終了時間": [end_time.strftime("%H:%M")],
        }
    )

    df_schedule = pd.concat([df_schedule, new_data], ignore_index=True)
    df_schedule.to_csv(csv_file_path, index=False)

    st.success(f"{add_date.strftime('%Y-%m-%d')}に「{task_name}」を追加しました！")
    st.rerun()

# ==========================================
# --- 6. 24時間のタイムスケジュール表示 ---
# ==========================================
st.header(f"⏳ {view_date_str} の24時間タイムスケジュール")

hours_list = [f"{str(i).zfill(2)}:00" for i in range(24)]
timeline_df = pd.DataFrame({"時間": hours_list, "予定": [""] * 24})

if not day_schedule.empty:
    for index, row in day_schedule.iterrows():
        start_hour_str = str(row["開始時間"])[:2]
        target_time = f"{start_hour_str}:00"
        condition = timeline_df["時間"] == target_time
        current_task = timeline_df.loc[condition, "予定"].values[0]

        if current_task == "":
            timeline_df.loc[condition, "予定"] = row["タスク"]
        else:
            timeline_df.loc[condition, "予定"] = current_task + " / " + row["タスク"]

st.table(timeline_df)

# ==========================================
# --- 7. スケジュールの時計型円グラフ ---
# ==========================================
st.header(f"📊 {view_date_str} の24時間円グラフ")

if not day_schedule.empty:
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

            # 【文字設定】時間の部分を <b>（太字）で囲んでいます
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

    # --- 【強化版】文字サイズの確実な変更 ---
    fig.update_traces(
        sort=False,
        direction="clockwise",
        rotation=90,
        texttemplate="%{customdata[0]}",
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textposition="inside",
        # グラフ内部のフォントサイズを「20」に強制します
        insidetextfont=dict(size=20),
        textfont_size=20,
    )

    fig.update_layout(showlegend=False)

    st.plotly_chart(fig)
else:
    st.write("この日の予定を追加すると、ここに円グラフが表示されます。")
