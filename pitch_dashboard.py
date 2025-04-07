import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, date

# 전체 30개 MLB 팀
teams = ['BAL', 'LAA', 'MIL', 'SF', 'PIT', 'DET', 'SEA', 'COL', 'AZ', 'TOR',
         'CWS', 'NYM', 'ATL', 'STL', 'KC', 'PHI', 'MIN', 'BOS', 'CLE', 'NYY',
         'WSH', 'TB', 'CIN', 'CHC', 'HOU', 'MIA', 'TEX', 'SD', 'OAK', 'LAD', 'ARI']

# 페이지 설정
st.set_page_config(layout="wide")
st.title("? MLB 투수 투구수 분석 대시보드")

# 날짜 범위 선택
start_date = st.date_input("시작 날짜", value=date(2025, 4, 1))
end_date = st.date_input("종료 날짜", value=date(2025, 4, 5))

# 팀 선택
selected_team = st.selectbox("팀 선택", teams)

# CSV 데이터 불러오기 (requests로 Google Drive 파일 읽기)
@st.cache_data
def load_data():
    file_id = "1sWJCEA7MUrOCGfj61ES1JQHJGBfYVYN3"
    url = f"https://drive.google.com/uc?id={file_id}"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("데이터를 불러오는 데 실패했습니다.")
        return pd.DataFrame()
    csv_data = StringIO(response.text)
    df = pd.read_csv(csv_data)
    df = df[df['game_type'] == 'R']
    df['game_date'] = pd.to_datetime(df['game_date'])
    return df

df = load_data()
if df.empty:
    st.stop()

df = df.set_index('game_date')
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
    if isinstance(val, (int, float)) and val >= 70:
        style += 'background-color: #ff9999;'  # 빨간색
    b2b_dates = highlight_info.get(col, set())
    if isinstance(date_val, date) and date_val in b2b_dates:
        style += 'background-color: #add8e6;'  # 파란색
    return style

# 스타일 지정
styled = df_pivot.style.set_caption(f"{selected_team} 팀 투구수 ({start_date} ~ {end_date})") \
    .set_properties(**{'text-align': 'center', 'padding': '8px', 'line-height': '1.6'}) \
    .set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('padding', '8px'), ('line-height', '1.6')]},
        {'selector': 'td', 'props': [('padding', '8px'), ('line-height', '1.6')]}
    ]) \
    .apply(lambda df: df.apply(lambda col: [
        highlight_cells(val, row, col.name, date_val=row if isinstance(row, date) else None, team=selected_team)
        for row, val in zip(df.index, col)
    ], axis=0), axis=None)

# 표시
st.write(styled.to_html(), unsafe_allow_html=True)

