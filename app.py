import streamlit as st
import pandas as pd
from datetime import time
import os

# --- 1. 画面のタイトル ---
st.title("私のタイムスケジュール帳")

# --- 2. データの保存先（パラメータの設定） ---
# ここで保存するファイルの名前を決めています
csv_file_path = "schedule.csv"


# --- 3. データを読み込む仕組み ---
def load_data():
    # もしすでにCSVファイルが存在していれば、それを読み込みます
    if os.path.exists(csv_file_path):
        return pd.read_csv(csv_file_path)
    # ファイルがなければ、空の表（データフレーム）を作ります
    else:
        return pd.DataFrame(columns=["タスク", "開始時間", "終了時間"])


# アプリが開かれたときに、データを読み込んで変数に格納します
df_schedule = load_data()

# --- 4. スケジュールの入力欄 ---
st.header("予定の追加")

# 入力用の部品です
task_name = st.text_input("タスク名", "プログラミング学習")
start_time = st.time_input("開始時間", time(9, 0))
end_time = st.time_input("終了時間", time(10, 0))

# --- 5. 追加ボタンと保存のロジック ---
if st.button("スケジュールに追加する"):
    # 新しく入力された予定を、表の形式に変換します
    new_data = pd.DataFrame(
        {
            "タスク": [task_name],
            "開始時間": [start_time.strftime("%H:%M")],  # 時間を文字の形式に整えます
            "終了時間": [end_time.strftime("%H:%M")],
        }
    )

    # 古いデータ（df_schedule）の下に、新しいデータ（new_data）をくっつけます
    df_schedule = pd.concat([df_schedule, new_data], ignore_index=True)

    # 結合した新しい表を、CSVファイルとして上書き保存します
    # index=False は、行番号（0, 1, 2...）をファイルに保存しないという設定です
    df_schedule.to_csv(csv_file_path, index=False)

    # 画面に成功メッセージを出します
    st.success(f"「{task_name}」を追加し、データを保存しました！")

# --- 6. スケジュールの一覧表示 ---
st.header("今日のスケジュール")

# 表の中にデータが入っているか（空ではないか）を確認します
if not df_schedule.empty:
    # データがあれば表を表示します
    st.table(df_schedule)
else:
    st.write("まだ予定は登録されていません。")
