import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import requests
import gdown

teams = ['LAD', 'SD', 'SF', 'AZ', 'COL',
         'CHC', 'MIL', 'STL', 'CIN', 'PIT',
         'PHI', 'NYM', 'MIA', 'WSH', 'ATL',
         'NYY', 'BOS', 'TOR', 'TB', 'BAL',
         'DET', 'KC', 'CLE', 'MIN', 'CWS',
         'TEX', 'LAA', 'HOU', 'ATH', 'SEA']

st.set_page_config(layout="wide")
st.title("⚾ MLB 2025 - Pitches by Game")

with st.expander("ℹ️ HELP"):
    st.markdown("""
    **This dashboard shows the number of pitches thrown by each team's pitchers in the 2025 MLB regular season, game by game.**

    - Select Team: Choose the team you want to analyze.
    - Start/End Date: Specify the date range for your analysis.
    - Red cells: The pitcher threw 60 or more pitches in a single game.
    - Blue cells: Indicates a back-to-back appearance (pitched on consecutive days).
    - Total: Total number of pitches by the pitcher during the selected period.
    - Back-to-Back: Number of back-to-back appearances during the selected period.

    **MLB 2025 각 팀 투수의 투구 수를 경기별로 나타냅니다.**

    - Select Team: 분석할 팀을 선택합니다.
    - Start/End Date: 원하는 날짜 범위를 지정합니다.
    - 빨간색 셀: 한 경기에서 60구 이상을 던진 경우.
    - 파란색 셀: 연투(Back-to-Back)가 발생한 경우.
    - Total: 해당 투수의 기간 내 총 투구 수
    - Back-to-Back: 해당 투수의 기간 내 연투 횟수
    """)

st.caption("🧑🏻‍💻 App developed by Kyengwook  |  📬 kyengwook8@naver.com  |  [GitHub](https://github.com/kyengwook/kyengwook)  |  [Instagram](https://instagram.com/kyengwook)")
st.caption("📊 Data source: [Baseball Savant](https://baseballsavant.mlb.com/) – MLB 2025 regular season data.")

selected_team = st.selectbox("Select Team", teams)
start_date = st.date_input("Start Date", value=date(2025, 6, 16))
end_date = st.date_input("End Date", value=date(2025, 7, 16))

if st.button("🔄 Update"):
    st.cache_data.clear()
    st.experimental_rerun()

@st.cache_data
def load_data_from_drive():
    url = 'https://drive.google.com/uc?id=1vZB9axWHpzUB5ixNG9Q3JtxTxQsCDMD4'
    output = 'data.csv'
    gdown.download(url, output, quiet=False)
    df = pd.read_csv(output)
    df = df[df['game_type'] == 'R']
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df.set_index('game_date').sort_index()
    return df

df = load_data_from_drive()

# 날짜 유효성 검사
if df.index.min() > pd.to_datetime(start_date) or df.index.max() < pd.to_datetime(end_date):
    st.warning("선택한 날짜 범위에 해당하는 데이터가 없습니다.")
    st.stop()

# 날짜 필터링
df_filtered = df.loc[str(start_date):str(end_date)].copy()

# 팀 필터링
df_team = df_filtered[
    ((df_filtered['away_team'] == selected_team) & (df_filtered['inning_topbot'] == 'Bot')) |
    ((df_filtered['home_team'] == selected_team) & (df_filtered['inning_topbot'] == 'Top'))
]

# 피벗 테이블 생성
df_pivot = df_team.groupby(['game_date', 'player_name']).size().reset_index(name='pitch_count')
df_pivot = df_pivot.pivot(index='game_date', columns='player_name', values='pitch_count').fillna(0).astype(int)
df_pivot.index = df_pivot.index.date
df_pivot.columns.name = "Player name"

# 날짜 전체 생성
all_dates = pd.date_range(start=start_date, end=end_date).date
existing_dates = set(df_pivot.index)
off_days = [d for d in all_dates if d not in existing_dates]

# OFF DAY 행 추가 (숫자 0으로)
off_day_rows = pd.DataFrame(0, index=off_days, columns=df_pivot.columns)
df_pivot = pd.concat([df_pivot, off_day_rows])
df_pivot = df_pivot.sort_index()

# Total & Back-to-Back 계산 전용 df (OFF DAY 포함)
column_totals = df_pivot.sum().sort_values(ascending=False)
df_pivot = df_pivot[column_totals.index]

# 연투 계산 함수
def calculate_consecutive_counts_and_dates(df_pivot_data):
    b2b = {}
    highlight_dates = {}
    for col in df_pivot_data.columns:
        pitch_series = df_pivot_data[col]
        pitched_days = pitch_series[pitch_series > 0].index.tolist()
        b2b_count = 0
        b2b_highlight_dates = set()
        for i in range(1, len(pitched_days)):
            d1, d2 = pitched_days[i - 1], pitched_days[i]
            if (d2 - d1).days == 1:
                b2b_count += 1
                b2b_highlight_dates.update([d1, d2])
        b2b[col] = b2b_count
        highlight_dates[col] = b2b_highlight_dates
    return b2b, highlight_dates

# Total 및 Back-to-Back 추가
df_pivot.loc['Total'] = df_pivot.sum()
b2b, highlight_info = calculate_consecutive_counts_and_dates(df_pivot.loc[df_pivot.index != 'Total'])

df_pivot.loc['Back-to-Back'] = pd.Series(b2b)

# 📌 OFF DAY 시 표시용 텍스트로 대체
df_display = df_pivot.copy()
for d in off_days:
    df_display.loc[d] = ['DAY OFF'] * df_display.shape[1]

# 셀 강조 함수
def highlight_cells(val, row, col, date_val):
    style = ''
    if row in ['Total', 'Back-to-Back']:
        return ''
    if isinstance(val, (int, float)) and val >= 60:
        style += 'background-color: #ff9999;'
    if isinstance(date_val, date) and date_val in highlight_info.get(col, set()):
        style += 'background-color: #add8e6;'
    if isinstance(date_val, date) and date_val in off_days:
        style += 'color: gray; font-style: italic; background-color: #f0f0f0;'
    return style

# 스타일링
styled = df_display.style.set_caption(f"📊{selected_team} Pitches by Game ({start_date} ~ {end_date})") \
    .set_properties(**{'text-align': 'center', 'padding': '8px', 'line-height': '1.6'}) \
    .set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('padding', '8px'), ('line-height', '1.6')]},
        {'selector': 'td', 'props': [('padding', '8px'), ('line-height', '1.6')]}
    ]) \
    .apply(lambda df: df.apply(lambda col: [
        highlight_cells(val, row, col.name, date_val=row if isinstance(row, date) else None)
        for row, val in zip(df.index, col)
    ], axis=0), axis=None)

# 출력
st.write(styled.to_html(), unsafe_allow_html=True)
