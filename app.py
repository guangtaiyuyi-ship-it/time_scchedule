import streamlit as st
import pandas as pd
from datetime import time, datetime
import os
import plotly.express as px  # グラフを作成するための新しいツールです

# --- 1. 画面のタイトル ---
st.title("私のタイムスケジュール帳")

# --- 2. データの保存先 ---
csv_file_path = "schedule.csv"


# --- 3. データを読み込む仕組み ---
def load_data():
    if os.path.exists(csv_file_path):
        return pd.read_csv(csv_file_path)
    else:
        return pd.DataFrame(columns=["タスク", "開始時間", "終了時間"])


df_schedule = load_data()

# --- 4. スケジュールの入力欄 ---
st.header("予定の追加")

task_name = st.text_input("タスク名", "プログラミング学習")
start_time = st.time_input("開始時間", time(9, 0))
end_time = st.time_input("終了時間", time(10, 0))

# --- 5. 追加ボタンと保存のロジック ---
if st.button("スケジュールに追加する"):
    new_data = pd.DataFrame(
        {
            "タスク": [task_name],
            "開始時間": [start_time.strftime("%H:%M")],
            "終了時間": [end_time.strftime("%H:%M")],
        }
    )

    df_schedule = pd.concat([df_schedule, new_data], ignore_index=True)
    df_schedule.to_csv(csv_file_path, index=False)

    st.success(f"「{task_name}」を追加し、データを保存しました！")

# --- 6. 24時間のタイムスケジュール表示 ---
st.header("24時間のタイムスケジュール")

hours_list = [f"{str(i).zfill(2)}:00" for i in range(24)]
timeline_df = pd.DataFrame({"時間": hours_list, "予定": [""] * 24})

if not df_schedule.empty:
    for index, row in df_schedule.iterrows():
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
# --- 7. スケジュールの割合（円グラフ）を追加 ---
# ==========================================
st.header("一日の時間の使い方（円グラフ）")

if not df_schedule.empty:
    task_durations = []
    task_names = []

    # 表のデータを1行ずつ計算します
    for index, row in df_schedule.iterrows():
        # datetime.strptime は、"09:00" のような文字を「時間データ」に変換する関数です
        start_dt = datetime.strptime(str(row["開始時間"]), "%H:%M")
        end_dt = datetime.strptime(str(row["終了時間"]), "%H:%M")

        # 終了時間から開始時間を引いて、かかった時間（秒）を出し、3600で割って「〇時間」にします
        if end_dt > start_dt:
            duration_hours = (end_dt - start_dt).seconds / 3600
            task_names.append(row["タスク"])
            task_durations.append(duration_hours)

    # グラフの元になるデータフレームを作ります
    chart_df = pd.DataFrame({"タスク": task_names, "時間（時間）": task_durations})

    # 【調整可能なパラメータ】: 同じ名前のタスクの時間を合計します
    chart_df = chart_df.groupby("タスク", as_index=False).sum()

    # 一日の合計時間を計算し、24時間に満たない場合は「空き時間」を追加します
    total_task_hours = chart_df["時間（時間）"].sum()
    if total_task_hours < 24:
        free_time_df = pd.DataFrame(
            {"タスク": ["空き時間"], "時間（時間）": [24 - total_task_hours]}
        )
        # タスクの表と空き時間の表をくっつけます
        chart_df = pd.concat([chart_df, free_time_df], ignore_index=True)

    # Plotlyを使って円グラフ（pie chart）を描きます
    # values: 大きさを決める列, names: ラベルになる列
    fig = px.pie(
        chart_df, values="時間（時間）", names="タスク", hole=0.3
    )  # hole=0.3でドーナツ型になります

    # アプリの画面にグラフを表示します
    st.plotly_chart(fig)
else:
    st.write("予定を追加すると、ここに円グラフが表示されます。")
