# 1. Import packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pybaseball import statcast_pitcher

# 2. Define function to calculate VAA
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

# 3. Get Statcast pitch data for a pitcher

#pitcher_id = 695243  
#start_date = '2025-03-28'
#end_date = '2025-09-30'

#df = statcast_pitcher(start_date, end_date, pitcher_id)

# Optional: Filter regular season only
df = statcast(start_dt='2025-03-18', end_dt='2025-08-23')
df = df[df['game_type'] == 'R']

# 4. Drop rows with missing physics data
df = df.dropna(subset=['vy0', 'ay', 'vz0', 'az'])

# 5. Calculate VAA and add to DataFrame
df['VAA'] = df.apply(lambda row: calculate_vaa(row['vy0'], row['ay'], row['vz0'], row['az']), axis=1)

# 6. Optional: Drop rows with NaN VAA
df = df.dropna(subset=['VAA', 'pitch_type'])


# 8. Optional: Print mean VAA per pitch type
vaa_summary = df.groupby('pitch_type')['VAA'].mean().sort_values()
print("\nAverage VAA by pitch type:")
print(vaa_summary.round(2))
