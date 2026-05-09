import streamlit as st
import pandas as pd
from datetime import time

# --- 1. 画面のタイトル ---
st.title("私のタイムスケジュール帳")

# --- 2. データの保存場所（変数）を準備 ---
# st.session_state は、アプリを操作している間、データを覚えておくためのStreamlitの機能です
if "schedule_list" not in st.session_state:
    st.session_state.schedule_list = []  # 最初は空のリスト（箱）を用意します

# --- 3. スケジュールの入力欄 ---
st.header("予定の追加")

# ユーザーが入力するための部品を用意します
task_name = st.text_input("タスク名", "プログラミング学習")
start_time = st.time_input("開始時間", time(9, 0))
end_time = st.time_input("終了時間", time(10, 0))

# --- 4. 追加ボタンとロジック（論理演算） ---
if st.button("スケジュールに追加する"):
    # ボタンが押されたら、入力されたデータを辞書型という形式でリストに追加します
    st.session_state.schedule_list.append(
        {"タスク": task_name, "開始": start_time, "終了": end_time}
    )
    # 成功したメッセージを表示します
    st.success(f"「{task_name}」を追加しました！")

# --- 5. スケジュールの一覧表示 ---
st.header("今日のスケジュール")

# リストの中にデータが1つ以上あるか（論理条件）を確認します
if len(st.session_state.schedule_list) > 0:
    # データを表（データフレーム）に変換して綺麗に表示します
    df = pd.DataFrame(st.session_state.schedule_list)
    st.table(df)
else:
    st.write("まだ予定は登録されていません。")
