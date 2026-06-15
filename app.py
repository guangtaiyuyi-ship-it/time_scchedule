import math
import os
from datetime import date, datetime, time, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

# --- 1. 画面のタイトルと基本設定 ---
st.set_page_config(page_title="タイムスケジュール帳", layout="wide")
st.title("私のタイムスケジュール帳")

# --- 2. データの保存先 ---
csv_file_path = "schedule.csv"
template_csv_path = "template_schedule.csv"
category_csv_path = "categories.csv"


# --- 3. データを読み込む仕組み ---
def load_category_data():
    if os.path.exists(category_csv_path):
        return pd.read_csv(category_csv_path)
    else:
        default_cats = pd.DataFrame(
            {
                "カテゴリ名": [
                    "大学の講義",
                    "プログラミング学習",
                    "プライベート",
                    "睡眠",
                    "仕事・バイト",
                    "未分類",
                    "空き時間",
                ],
                "色": [
                    "#1f77b4",
                    "#2ca02c",
                    "#ff7f0e",
                    "#9467bd",
                    "#d62728",
                    "#7f7f7f",
                    "#F4F4F4",
                ],
            }
        )
        default_cats.to_csv(category_csv_path, index=False)
        return default_cats


def load_data():
    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path)
        if "カテゴリ" not in df.columns:
            df["カテゴリ"] = "未分類"
        return df
    else:
        return pd.DataFrame(
            columns=["日付", "タスク", "開始時間", "終了時間", "カテゴリ"]
        )


DAY_ORDER = ["月", "火", "水", "木", "金", "土", "日"]


def sort_template(df):
    """テンプレートを曜日順→開始時間順にソートして返す"""
    if df.empty:
        return df
    df = df.copy()
    df["_day_order"] = df["曜日"].map({d: i for i, d in enumerate(DAY_ORDER)})
    df = df.sort_values(["_day_order", "開始時間"]).drop(columns=["_day_order"])
    return df.reset_index(drop=True)


def load_template_data():
    if os.path.exists(template_csv_path):
        df = pd.read_csv(template_csv_path)
        if "カテゴリ" not in df.columns:
            df["カテゴリ"] = "未分類"
        return sort_template(df)
    else:
        return pd.DataFrame(
            columns=["曜日", "タスク", "開始時間", "終了時間", "カテゴリ"]
        )


df_categories = load_category_data()
df_schedule = load_data()
df_template = load_template_data()

CATEGORIES = df_categories["カテゴリ名"].tolist()
CATEGORY_COLORS = dict(zip(df_categories["カテゴリ名"], df_categories["色"]))
selectable_categories = [c for c in CATEGORIES if c != "空き時間"]
PROTECTED_CATS = ["未分類", "空き時間"]


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def is_color_too_similar(new_hex, existing_hexes, threshold=40):
    new_rgb = hex_to_rgb(new_hex)
    for ex_hex in existing_hexes:
        ex_rgb = hex_to_rgb(ex_hex)
        distance = math.sqrt(
            (new_rgb[0] - ex_rgb[0]) ** 2
            + (new_rgb[1] - ex_rgb[1]) ** 2
            + (new_rgb[2] - ex_rgb[2]) ** 2
        )
        if distance < threshold:
            return True
    return False


def render_category_adder(key_prefix):
    with st.expander("➕ 新しいカテゴリを追加", expanded=False):
        new_cat_name = st.text_input("カテゴリ名", key=f"{key_prefix}_new_c_name")
        new_cat_color = st.color_picker(
            "色", "#00f900", key=f"{key_prefix}_new_c_color"
        )

        if st.button("追加して保存", key=f"{key_prefix}_add_btn"):
            used_colors = [
                color for cat, color in CATEGORY_COLORS.items() if cat != "空き時間"
            ]

            if new_cat_name in CATEGORIES:
                st.error("そのカテゴリはすでに存在します！")
            elif new_cat_name.strip() == "":
                st.error("カテゴリ名を入力してください。")
            elif is_color_too_similar(new_cat_color, used_colors):
                st.error(
                    "❌ その色はすでに使われているカテゴリと似すぎています！ 別の色を選んでください。"
                )
            else:
                new_cat_df = pd.DataFrame(
                    {"カテゴリ名": [new_cat_name], "色": [new_cat_color]}
                )
                temp_df = load_category_data()

                df_normal = temp_df[~temp_df["カテゴリ名"].isin(PROTECTED_CATS)]
                df_system = temp_df[temp_df["カテゴリ名"].isin(PROTECTED_CATS)]
                temp_df = pd.concat(
                    [df_normal, new_cat_df, df_system], ignore_index=True
                )

                temp_df.to_csv(category_csv_path, index=False)
                st.success(f"「{new_cat_name}」を追加しました！")
                st.rerun()


def is_overlapping(new_start_str, new_end_str, existing_df):
    if existing_df.empty:
        return False
    new_s = datetime.strptime(new_start_str, "%H:%M")
    new_e = datetime.strptime(new_end_str, "%H:%M")
    for _, row in existing_df.iterrows():
        ex_s = datetime.strptime(row["開始時間"], "%H:%M")
        ex_e = datetime.strptime(row["終了時間"], "%H:%M")
        if new_s < ex_e and new_e > ex_s:
            return True
    return False


# ==========================================
# --- 左側のサイドバー（テンプレート設定） ---
# ==========================================
st.sidebar.header("⚙️ 曜日ごとの基本テンプレート")
st.sidebar.subheader("➕ 新規登録")
temp_day = st.sidebar.selectbox(
    "曜日を選択", ["月", "火", "水", "木", "金", "土", "日"]
)

temp_cat = st.sidebar.selectbox("カテゴリ", selectable_categories, key="t_cat")
render_category_adder("sidebar")

temp_task = st.sidebar.text_input("タスク名", "ルーティン作業", key="t_task")

# ★ 修正ポイント: step=60 を指定して1分刻みに変更（時計の針やキーボードで自由に入力可能に）
temp_start = st.sidebar.time_input(
    "開始時間", time(7, 0), key="t_start", step=60
)
temp_end = st.sidebar.time_input("終了時間", time(8, 0), key="t_end", step=60)

if st.sidebar.button("テンプレートに登録する"):
    new_start_str = temp_start.strftime("%H:%M")
    new_end_str = temp_end.strftime("%H:%M")
    existing_temp = df_template[df_template["曜日"] == temp_day]

    if new_start_str >= new_end_str:
        st.sidebar.error("終了時間は開始時間より後にしてください。")
    elif is_overlapping(new_start_str, new_end_str, existing_temp):
        st.sidebar.error(
            f"{temp_day}曜のこの時間は、すでに別のテンプレートが入っています！"
        )
    else:
        new_temp = pd.DataFrame(
            {
                "曜日": [temp_day],
                "タスク": [temp_task],
                "開始時間": [new_start_str],
                "終了時間": [new_end_str],
                "カテゴリ": [temp_cat],
            }
        )
        df_template = sort_template(
            pd.concat([df_template, new_temp], ignore_index=True)
        )
        df_template.to_csv(template_csv_path, index=False)
        st.sidebar.success("登録しました！")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ 登録済みテンプレート")
if not df_template.empty:
    for index, row in df_template.iterrows():
        st.sidebar.markdown(
            f"<div style='white-space: nowrap; font-size: 14px;'><b>{row['曜日']}</b> {row['開始時間']}~{row['終了時間']} : {row['タスク']} ({row['カテゴリ']})</div>",
            unsafe_allow_html=True,
        )

        col_del, col_spacer = st.sidebar.columns([1, 2])
        with col_del:
            if st.button("削除", key=f"del_temp_{index}"):
                df_template = df_template.drop(index)
                df_template.to_csv(template_csv_path, index=False)
                st.rerun()

        # ==========================================
        # ★ テンプレート編集エクスパンダー
        # ==========================================
        with st.sidebar.expander(f"✏️ 編集", expanded=False):
            edit_t_day = st.selectbox(
                "曜日",
                ["月", "火", "水", "木", "金", "土", "日"],
                index=["月", "火", "水", "木", "金", "土", "日"].index(
                    row["曜日"]
                ),
                key=f"edit_t_day_{index}",
            )

            current_cat = row.get("カテゴリ", "未分類")
            cat_options = selectable_categories
            cat_index = (
                cat_options.index(current_cat)
                if current_cat in cat_options
                else 0
            )
            edit_t_cat = st.selectbox(
                "カテゴリ",
                cat_options,
                index=cat_index,
                key=f"edit_t_cat_{index}",
            )

            edit_t_task = st.text_input(
                "タスク名", row["タスク"], key=f"edit_t_task_{index}"
            )

            current_t_start = datetime.strptime(row["開始時間"], "%H:%M").time()
            current_t_end = datetime.strptime(row["終了時間"], "%H:%M").time()

            # ★ 修正ポイント: 編集画面でも step=60 を指定
            edit_t_start = st.time_input(
                "開始時間",
                current_t_start,
                key=f"edit_t_start_{index}",
                step=60,
            )
            edit_t_end = st.time_input(
                "終了時間", current_t_end, key=f"edit_t_end_{index}", step=60
            )

            if st.button("テンプレートを更新する", key=f"upd_temp_btn_{index}"):
                new_s_str = edit_t_start.strftime("%H:%M")
                new_e_str = edit_t_end.strftime("%H:%M")

                # 自分自身を除いた同じ曜日のテンプレートで重複チェック
                other_temps = df_template[
                    (df_template["曜日"] == edit_t_day)
                    & (df_template.index != index)
                ]

                if new_s_str >= new_e_str:
                    st.error("終了時間は開始時間より後にしてください。")
                elif is_overlapping(new_s_str, new_e_str, other_temps):
                    st.error(
                        f"❌ {edit_t_day}曜のこの時間帯には別のテンプレートが入っています！"
                    )
                else:
                    df_template.at[index, "曜日"] = edit_t_day
                    df_template.at[index, "タスク"] = edit_t_task
                    df_template.at[index, "開始時間"] = new_s_str
                    df_template.at[index, "終了時間"] = new_e_str
                    df_template.at[index, "カテゴリ"] = edit_t_cat
                    df_template = sort_template(df_template)
                    df_template.to_csv(template_csv_path, index=False)
                    st.success("✅ テンプレートを更新しました！")
                    st.rerun()

        st.sidebar.write("---")
else:
    st.sidebar.write("現在登録されているテンプレートはありません。")

# ==========================================
# --- カテゴリの管理（編集・削除） ---
# ==========================================
st.sidebar.subheader("🗑️・✏️ カテゴリの管理")
for index, row in df_categories.iterrows():
    cat_name = row["カテゴリ名"]

    if cat_name in PROTECTED_CATS:
        continue

    c1, c2 = st.sidebar.columns([3, 1])
    with c1:
        st.markdown(
            f"<div style='white-space: nowrap; font-size: 14px;'><span style='color:{row['色']};'>■</span> <b>{cat_name}</b></div>",
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("削除", key=f"del_cat_{index}"):
            df_categories = df_categories.drop(index)
            df_categories.to_csv(category_csv_path, index=False)

            if not df_schedule.empty and "カテゴリ" in df_schedule.columns:
                df_schedule.loc[
                    df_schedule["カテゴリ"] == cat_name, "カテゴリ"
                ] = "未分類"
                df_schedule.to_csv(csv_file_path, index=False)
            if not df_template.empty and "カテゴリ" in df_template.columns:
                df_template.loc[
                    df_template["カテゴリ"] == cat_name, "カテゴリ"
                ] = "未分類"
                df_template.to_csv(template_csv_path, index=False)

            st.rerun()

    with st.sidebar.expander("✏️ 編集", expanded=False):
        edit_c_name = st.text_input(
            "新しい名前", cat_name, key=f"edit_c_name_{index}"
        )
        edit_c_color = st.color_picker(
            "新しい色", row["色"], key=f"edit_c_color_{index}"
        )

        if st.button("更新する", key=f"upd_cat_btn_{index}"):
            used_colors = [
                c
                for name, c in CATEGORY_COLORS.items()
                if name != cat_name and name != "空き時間"
            ]

            if edit_c_name != cat_name and edit_c_name in CATEGORIES:
                st.error("その名前はすでに使われています。")
            elif edit_c_name.strip() == "":
                st.error("名前を入力してください。")
            elif edit_c_color != row["色"] and is_color_too_similar(
                edit_c_color, used_colors
            ):
                st.error("❌ その色は他のカテゴリと似すぎています！")
            else:
                df_categories.at[index, "カテゴリ名"] = edit_c_name
                df_categories.at[index, "色"] = edit_c_color
                df_categories.to_csv(category_csv_path, index=False)

                if edit_c_name != cat_name:
                    if (
                        not df_schedule.empty
                        and "カテゴリ" in df_schedule.columns
                    ):
                        df_schedule.loc[
                            df_schedule["カテゴリ"] == cat_name, "カテゴリ"
                        ] = edit_c_name
                        df_schedule.to_csv(csv_file_path, index=False)
                    if (
                        not df_template.empty
                        and "カテゴリ" in df_template.columns
                    ):
                        df_template.loc[
                            df_template["カテゴリ"] == cat_name, "カテゴリ"
                        ] = edit_c_name
                        df_template.to_csv(template_csv_path, index=False)

                st.success("カテゴリを更新しました！")
                st.rerun()


# ==========================================
# --- グラフを作る専用の機械 ---
# ==========================================
def create_pie_chart(day_schedule, font_size=14):
    if day_schedule.empty:
        return None

    day_schedule = day_schedule.sort_values(by="開始時間")
    pie_labels_unique = []
    pie_values = []
    display_texts = []
    slice_colors = []

    current_dt = datetime.strptime("00:00", "%H:%M")
    counter = 0

    for index, row in day_schedule.iterrows():
        start_dt = datetime.strptime(str(row["開始時間"]), "%H:%M")
        end_dt = datetime.strptime(str(row["終了時間"]), "%H:%M")

        if start_dt > current_dt:
            free_hours = (start_dt - current_dt).seconds / 3600
            pie_labels_unique.append(f"空き時間_{counter}")
            pie_values.append(free_hours)
            display_texts.append("")
            slice_colors.append(CATEGORY_COLORS.get("空き時間", "#F4F4F4"))
            counter += 1

        actual_start = max(start_dt, current_dt)
        if end_dt > actual_start:
            task_hours = (end_dt - actual_start).seconds / 3600
            pie_labels_unique.append(f"{row['タスク']}_{counter}")
            pie_values.append(task_hours)

            time_range_str = f"<b>{actual_start.strftime('%H:%M')}~{end_dt.strftime('%H:%M')}</b>"
            display_texts.append(f"{row['タスク']}<br>{time_range_str}")

            cat = row.get("カテゴリ", "未分類")
            slice_colors.append(
                CATEGORY_COLORS.get(
                    cat, CATEGORY_COLORS.get("未分類", "#7f7f7f")
                )
            )

            current_dt = end_dt
            counter += 1

    total_hours = sum(pie_values)
    if total_hours < 24:
        pie_labels_unique.append(f"空き時間_{counter}")
        pie_values.append(24 - total_hours)
        display_texts.append("")
        slice_colors.append(CATEGORY_COLORS.get("空き時間", "#F4F4F4"))

    chart_df = pd.DataFrame(
        {
            "一意な名前": pie_labels_unique,
            "時間（時間）": pie_values,
            "グラフ用テキスト": display_texts,
        }
    )

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
        marker=dict(colors=slice_colors, line=dict(color="#FFFFFF", width=2)),
        textposition="inside",
        textfont=dict(size=font_size),
    )
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    return fig


# ==========================================
# --- データの合体と一週間の日付計算 ---
# ==========================================
st.header("📅 表示する週の選択")
base_date = st.date_input("基準となる日付を選んでください", date.today())
start_of_week = base_date - timedelta(days=base_date.weekday())
week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
week_days_str = ["月", "火", "水", "木", "金", "土", "日"]


def get_combined_schedule(target_date_str, target_weekday_str):
    day_temp = (
        df_template[df_template["曜日"] == target_weekday_str].copy()
        if not df_template.empty
        else pd.DataFrame()
    )
    day_spec = (
        df_schedule[df_schedule["日付"] == target_date_str].copy()
        if not df_schedule.empty
        else pd.DataFrame()
    )
    return pd.concat([day_temp, day_spec], ignore_index=True)


# ==========================================
# --- ワークライフバランス分析レポート ---
# ==========================================
st.header("📈 今週のワークライフバランス分析")
weekly_combined_data = pd.DataFrame()
for i in range(7):
    day_data = get_combined_schedule(
        week_dates[i].strftime("%Y-%m-%d"), week_days_str[i]
    )
    weekly_combined_data = pd.concat(
        [weekly_combined_data, day_data], ignore_index=True
    )

if not weekly_combined_data.empty:
    weekly_combined_data["時間（時間）"] = weekly_combined_data.apply(
        lambda row: (
            datetime.strptime(row["終了時間"], "%H:%M")
            - datetime.strptime(row["開始時間"], "%H:%M")
        ).seconds
        / 3600,
        axis=1,
    )
    summary_df = (
        weekly_combined_data.groupby("カテゴリ")["時間（時間）"].sum().reset_index()
    )
    fig_bar = px.bar(
        summary_df,
        x="時間（時間）",
        y="カテゴリ",
        orientation="h",
        color="カテゴリ",
        color_discrete_map=CATEGORY_COLORS,
        text="時間（時間）",
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}h", textposition="auto")
    fig_bar.update_layout(
        showlegend=False, height=250, margin=dict(t=10, b=10, l=10, r=10)
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.write("予定を追加すると、ここに時間の使い方の分析グラフが表示されます。")

st.write("---")

# ==========================================
# --- 一週間のダッシュボード ---
# ==========================================
st.header("📊 今週のスケジュール全体図")
cols_top = st.columns(4)
cols_bottom = st.columns(4)

for i in range(7):
    current_date_str = week_dates[i].strftime("%Y-%m-%d")
    current_weekday_str = week_days_str[i]
    day_schedule = get_combined_schedule(current_date_str, current_weekday_str)
    target_col = cols_top[i] if i < 4 else cols_bottom[i - 4]

    with target_col:
        st.markdown(f"**{current_weekday_str} ({week_dates[i].strftime('%m/%d')})**")
        fig = create_pie_chart(day_schedule, font_size=12)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"dash_chart_{i}")
        else:
            st.write("予定なし")

st.write("---")

# ==========================================
# --- 曜日ごとの編集タブ ---
# ==========================================
st.header("✏️ 日ごとの個別予定編集")
tabs = st.tabs(
    [
        f"{week_days_str[i]} ({week_dates[i].strftime('%m/%d')})"
        for i in range(7)
    ]
)

for i in range(7):
    current_date_str = week_dates[i].strftime("%Y-%m-%d")
    current_weekday_str = week_days_str[i]

    with tabs[i]:
        st.subheader(f"📝 {current_date_str} の予定追加")
        col_cat, col_task, col_start, col_end = st.columns(4)

        with col_cat:
            task_cat = st.selectbox("カテゴリ", selectable_categories, key=f"cat_{i}")

        with col_task:
            task_name = st.text_input("タスク名", "打ち合わせ", key=f"task_{i}")
        with col_start:
            # ★ 修正ポイント: step=60 を指定して1分刻みに変更
            start_time = st.time_input(
                "開始時間", time(13, 0), key=f"start_{i}", step=60
            )
        with col_end:
            # ★ 修正ポイント: step=60 を指定して1分刻みに変更
            end_time = st.time_input(
                "終了時間", time(14, 0), key=f"end_{i}", step=60
            )

        if st.button("個別の予定を追加する", key=f"btn_{i}"):
            new_start_str = start_time.strftime("%H:%M")
            new_end_str = end_time.strftime("%H:%M")

            existing_combined = get_combined_schedule(
                current_date_str, current_weekday_str
            )

            if new_start_str >= new_end_str:
                st.error("終了時間は開始時間より後にしてください。")
            elif is_overlapping(new_start_str, new_end_str, existing_combined):
                st.error(
                    "エラー：指定した時間帯には、すでに別の予定（またはテンプレート）が入っています！"
                )
            else:
                new_data = pd.DataFrame(
                    {
                        "日付": [current_date_str],
                        "タスク": [task_name],
                        "開始時間": [new_start_str],
                        "終了時間": [new_end_str],
                        "カテゴリ": [task_cat],
                    }
                )
                df_schedule = pd.concat(
                    [df_schedule, new_data], ignore_index=True
                )
                df_schedule.to_csv(csv_file_path, index=False)
                st.success("予定を追加しました！")
                st.rerun()

        st.markdown("---")

        # ==========================================
        # --- 個別予定の管理（削除・編集） ---
        # ==========================================
        st.subheader("🗑️・✏️ この日の個別予定の管理")
        if not df_schedule.empty and "日付" in df_schedule.columns:
            today_tasks = df_schedule[df_schedule["日付"] == current_date_str]
            if not today_tasks.empty:
                for index, row in today_tasks.iterrows():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(
                            f"**{row['開始時間']}~{row['終了時間']}** : {row['タスク']} ({row.get('カテゴリ', '未分類')})"
                        )
                    with c2:
                        if st.button("削除", key=f"del_task_{index}_{i}"):
                            df_schedule = df_schedule.drop(index)
                            df_schedule.to_csv(csv_file_path, index=False)
                            st.rerun()

                    with st.expander(
                        f"✏️ 「{row['タスク']}」の時間を編集", expanded=False
                    ):
                        current_s_time = datetime.strptime(
                            row["開始時間"], "%H:%M"
                        ).time()
                        current_e_time = datetime.strptime(
                            row["終了時間"], "%H:%M"
                        ).time()

                        # ★ 修正ポイント: 編集画面でも step=60 を指定
                        edit_s = st.time_input(
                            "新しい開始時間",
                            current_s_time,
                            key=f"edit_s_{index}_{i}",
                            step=60,
                        )
                        edit_e = st.time_input(
                            "新しい終了時間",
                            current_e_time,
                            key=f"edit_e_{index}_{i}",
                            step=60,
                        )

                        if st.button(
                            "時間を更新する", key=f"update_{index}_{i}"
                        ):
                            new_s_str = edit_s.strftime("%H:%M")
                            new_e_str = edit_e.strftime("%H:%M")

                            temp_df_schedule = df_schedule.drop(index)
                            day_temp = (
                                df_template[
                                    df_template["曜日"] == current_weekday_str
                                ].copy()
                                if not df_template.empty
                                else pd.DataFrame()
                            )
                            day_spec = (
                                temp_df_schedule[
                                    temp_df_schedule["日付"] == current_date_str
                                ].copy()
                                if not temp_df_schedule.empty
                                else pd.DataFrame()
                            )
                            existing_combined = pd.concat(
                                [day_temp, day_spec], ignore_index=True
                            )

                            if new_s_str >= new_e_str:
                                st.error("終了時間は開始時間より後にしてください。")
                            elif is_overlapping(
                                new_s_str, new_e_str, existing_combined
                            ):
                                st.error(
                                    "エラー：変更後の時間が他の予定と重なっています！"
                                )
                            else:
                                df_schedule.at[index, "開始時間"] = new_s_str
                                df_schedule.at[index, "終了時間"] = new_e_str
                                df_schedule.to_csv(csv_file_path, index=False)
                                st.success("時間を更新しました！")
                                st.rerun()
                    st.write("---")
            else:
                st.write("この日に追加された個別予定はありません。")
        else:
            st.write("この日に追加された個別予定はありません。")

        st.markdown("---")
        day_schedule = get_combined_schedule(
            current_date_str, current_weekday_str
        )
        st.subheader("📊 この日の詳細グラフ（基本＋個別）")
        big_fig = create_pie_chart(day_schedule, font_size=18)
        if big_fig:
            st.plotly_chart(
                big_fig, use_container_width=True, key=f"tab_chart_{i}"
            )
        else:
            st.write("予定を追加するとグラフが表示されます。")