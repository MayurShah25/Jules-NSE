import pandas as pd
import numpy as np

# create df with 2 rows
df = pd.DataFrame({'high': [100, 105], 'low': [90, 95]})
print("Len > 1")
print(df.iloc[-31:-1])

# create df with 1 row
df2 = pd.DataFrame({'high': [100], 'low': [90]})
print("Len == 1")
print(df2.iloc[-31:-1])
