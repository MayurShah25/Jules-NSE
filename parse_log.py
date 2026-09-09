with open('september_backtest.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Trading Day:" in line:
        date = line.split("Trading Day: ")[1].strip()
        print(f"\n--- {date} ---")
    if "BACKTEST SUMMARY" in line:
        for j in range(1, 5):
            if i+j < len(lines):
                print(lines[i+j].strip().split(' - ')[-1])
