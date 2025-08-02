import pandas as pd
import numpy as np
from pybaseball import statcast
from pybaseball import statcast_pitcher

# function to calculate VAA
def calculate_vaa(vy0, ay, vz0, az, y0=50.0, yf=17.0/12.0):
    try:
        # Final y-velocity at home plate
        vy_f = -np.sqrt(vy0**2 - 2 * ay * (y0 - yf))
    except:
        return np.nan
    t = (vy_f - vy0) / ay  # Time to reach home plate
    vz_f = vz0 + az * t    # Final z-velocity
    vaa = -np.arctan(vz_f / vy_f) * (180 / np.pi)
    return vaa


#df = statcast_pitcher(start_date, end_date, pitcher_id)
df = statcast(start_dt='2025-03-18', end_dt='2025-08-23')
df = df[df['game_type'] == 'R']

df = df.dropna(subset=['vy0', 'ay', 'vz0', 'az'])

df['VAA'] = df.apply(lambda row: calculate_vaa(row['vy0'], row['ay'], row['vz0'], row['az']), axis=1)

df = df.dropna(subset=['VAA', 'pitch_type'])


#summary
vaa_summary = df.groupby('pitch_type')['VAA'].mean().sort_values()
print("\nAverage VAA by pitch type:")
print(vaa_summary.round(2))
