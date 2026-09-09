import pandas as pd
import numpy as np

# create df with 2 rows
df = pd.DataFrame({'high': [100, 105], 'low': [90, 95]})
print("Len == 2, iloc[-31:-1]")
print(df.iloc[-31:-1])

# create df with 3 rows
df = pd.DataFrame({'high': [100, 105, 110], 'low': [90, 95, 100]})
print("Len == 3, iloc[-31:-1]")
print(df.iloc[-31:-1])
