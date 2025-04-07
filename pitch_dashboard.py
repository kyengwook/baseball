import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, date

# ��ü 30�� MLB ��
teams = ['BAL', 'LAA', 'MIL', 'SF', 'PIT', 'DET', 'SEA', 'COL', 'AZ', 'TOR',
         'CWS', 'NYM', 'ATL', 'STL', 'KC', 'PHI', 'MIN', 'BOS', 'CLE', 'NYY',
         'WSH', 'TB', 'CIN', 'CHC', 'HOU', 'MIA', 'TEX', 'SD', 'OAK', 'LAD', 'ARI']

# ������ ����
st.set_page_config(layout="wide")
st.title("? MLB ���� ������ �м� ��ú���")

# ��¥ ���� ����
start_date = st.date_input("���� ��¥", value=date(2025, 4, 1))
end_date = st.date_input("���� ��¥", value=date(2025, 4, 5))

# �� ����
selected_team = st.selectbox("�� ����", teams)

# CSV ������ �ҷ����� (requests�� Google Drive ���� �б�)
@st.cache_data
def load_data():
    file_id = "1sWJCEA7MUrOCGfj61ES1JQHJGBfYVYN3"
    url = f"https://drive.google.com/uc?id={file_id}"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("�����͸� �ҷ����� �� �����߽��ϴ�.")
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

# ���� ��� �Լ�
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

# �� ���͸�
df_team = df_filtered[
    ((df_filtered['away_team'] == selected_team) & (df_filtered['inning_topbot'] == 'Bot')) |
    ((df_filtered['home_team'] == selected_team) & (df_filtered['inning_topbot'] == 'Top'))
]

# �ǹ� ���̺� ����
df_pivot = df_team.groupby(['game_date', 'player_name']).size().reset_index(name='pitch_count')
df_pivot = df_pivot.pivot(index='game_date', columns='player_name', values='pitch_count').fillna(0).astype(int)
df_pivot.index = df_pivot.index.date

# �� ����
column_totals = df_pivot.sum().sort_values(ascending=False)
df_pivot = df_pivot[column_totals.index]

# ���� �� ���� ���
df_pivot.loc['Total'] = df_pivot.sum()
b2b, highlight_info = calculate_consecutive_counts_and_dates(df_pivot.iloc[:-1])
df_pivot.loc['Back-to-Back'] = pd.Series(b2b)

# �� ���� �Լ�
def highlight_cells(val, row, col, date_val, team):
    style = ''
    if row in ['Total', 'Back-to-Back']:
        return ''
    if isinstance(val, (int, float)) and val >= 70:
        style += 'background-color: #ff9999;'  # ������
    b2b_dates = highlight_info.get(col, set())
    if isinstance(date_val, date) and date_val in b2b_dates:
        style += 'background-color: #add8e6;'  # �Ķ���
    return style

# ��Ÿ�� ����
styled = df_pivot.style.set_caption(f"{selected_team} �� ������ ({start_date} ~ {end_date})") \
    .set_properties(**{'text-align': 'center', 'padding': '8px', 'line-height': '1.6'}) \
    .set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('padding', '8px'), ('line-height', '1.6')]},
        {'selector': 'td', 'props': [('padding', '8px'), ('line-height', '1.6')]}
    ]) \
    .apply(lambda df: df.apply(lambda col: [
        highlight_cells(val, row, col.name, date_val=row if isinstance(row, date) else None, team=selected_team)
        for row, val in zip(df.index, col)
    ], axis=0), axis=None)

# ǥ��
st.write(styled.to_html(), unsafe_allow_html=True)

