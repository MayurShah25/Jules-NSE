import re

def print_summary(filename, month_name):
    with open(filename, 'r') as f:
        text = f.read()

    daily_starts = re.findall(r'📅 Trading Day: (.*?)\n💰 Starting Capital Today: ₹([-0-9.]+)', text)
    pnl_matches = re.findall(r'Net PnL:\s+([-0-9.]+)', text)
    pnl_matches = pnl_matches[:-1] if len(pnl_matches) > len(daily_starts) else pnl_matches

    print(f"### 📉 {month_name.upper()} 2026")
    print("| Date | Starting Capital | Daily Net PNL | End of Day Capital |")
    print("| :--- | :--- | :--- | :--- |")
    for i, start in enumerate(daily_starts):
        date = start[0]
        cap = float(start[1])
        if i < len(pnl_matches):
            pnl = float(pnl_matches[i])
            end_cap = cap + pnl
            color = "<span style=\"color:green\">**+₹" if pnl >= 0 else "<span style=\"color:red\">**-₹"
            formatted_pnl = f"{abs(pnl):,.2f}"
            print(f"| **{date[5:]}** | ₹{cap:,.2f} | {color}{formatted_pnl}**</span> | ₹{end_cap:,.2f} |")

    final_return = re.search(r'Total Return: ([-0-9.]+%)\nFinal Capital: ₹([-0-9.]+)', text)
    if final_return:
        print(f"\n**Total Return:** {final_return.group(1)}")
        print(f"**Final Capital:** ₹{float(final_return.group(2)):,.2f}\n")
