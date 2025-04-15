import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import requests


teams = ['LAD', 'SD', 'SF', 'AZ', 'COL',
         'CHC', 'MIL', 'STL', 'CIN', 'PIT',
         'PHI', 'NYM', 'MIA', 'WSH', 'ATL',
         'NYY', 'BOS', 'TOR', 'TB', 'BAL',
         'DET', 'KC', 'CLE', 'MIN', 'CWS',
         'TEX', 'LAA', 'HOU', 'ATH', 'SEA']
         


st.set_page_config(layout="wide")
st.title("⚾ MLB Pitches by Game")

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
         
# 팀 선택
selected_team = st.selectbox("Select Team", teams)
# 날짜 범위 선택
start_date = st.date_input("Start Date", value=date(2025, 3, 18))
end_date = st.date_input("End Date", value=date(2025, 4, 13))

# 새로고침 버튼
#if st.button("🔄 Update"):
    #st.cache_data.clear()
    #st.experimental_rerun()

# CSV 데이터 로드
@st.cache_data
def load_data_from_drive():
    file_id = "1sWJCEA7MUrOCGfj61ES1JQHJGBfYVYN3"  
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(download_url)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.content.decode("utf-8")), encoding='utf-8')
    df = df[df['game_type'] == 'R']
    df['game_date'] = pd.to_datetime(df['game_date'])
    df = df.set_index('game_date').sort_index()
    return df

# 데이터 불러오기
df = load_data_from_drive()

# 날짜 범위 확인
if df.index.min() > pd.to_datetime(start_date) or df.index.max() < pd.to_datetime(end_date):
    st.warning("선택한 날짜 범위에 해당하는 데이터가 없습니다.")
    st.stop()

# 날짜로 필터링
df_filtered = df.loc[str(start_date):str(end_date)].copy()

# 연투 계산 함수
def calculate_consecutive_counts_and_dates(df_pivot):
    b2b = {}
    highlight_dates = {}
    for col in df_pivot.columns:
        pitch_series = df_pivot[col]
        pitched_days = pitch_series[pitch_series > 0].index.tolist()
        b2b_count = 0
        b2b_highlight_dates = set()
        for i in range(1, len(pitched_days)):
            d1, d2 = pitched_days[i-1], pitched_days[i]
            if (d2 - d1).days == 1:
                b2b_count += 1
                b2b_highlight_dates.update([d1, d2])
        b2b[col] = b2b_count
        highlight_dates[col] = b2b_highlight_dates
    return b2b, highlight_dates

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

# 열 정렬
column_totals = df_pivot.sum().sort_values(ascending=False)
df_pivot = df_pivot[column_totals.index]

# 총합 및 연투 계산
df_pivot.loc['Total'] = df_pivot.sum()
b2b, highlight_info = calculate_consecutive_counts_and_dates(df_pivot.iloc[:-1])
df_pivot.loc['Back-to-Back'] = pd.Series(b2b)

# 셀 강조 함수
def highlight_cells(val, row, col, date_val, team):
    style = ''
    if row in ['Total', 'Back-to-Back']:
        return ''
    if isinstance(val, (int, float)) and val >= 60:
        style += 'background-color: #ff9999;'  # 빨간색
    b2b_dates = highlight_info.get(col, set())
    if isinstance(date_val, date) and date_val in b2b_dates:
        style += 'background-color: #add8e6;'  # 파란색
    return style

# 스타일 지정
styled = df_pivot.style.set_caption(f"📊{selected_team} Pitches by Game ({start_date} ~ {end_date})") \
    .set_properties(**{'text-align': 'center', 'padding': '8px', 'line-height': '1.6'}) \
    .set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('padding', '8px'), ('line-height', '1.6')]},
        {'selector': 'td', 'props': [('padding', '8px'), ('line-height', '1.6')]}
    ]) \
    .apply(lambda df: df.apply(lambda col: [
        highlight_cells(val, row, col.name, date_val=row if isinstance(row, date) else None, team=selected_team)
        for row, val in zip(df.index, col)
    ], axis=0), axis=None)


# 결과 표시
st.write(styled.to_html(), unsafe_allow_html=True)
