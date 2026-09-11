import sys

def parse_log(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Date\tStarting Capital\tDaily Net PNL\tEnd of Day Capital")

    current_date = ""
    capitals = []

    for i, line in enumerate(lines):
        if "Trading Day:" in line:
            current_date = line.split("Trading Day: ")[1].strip()
        if "Starting Capital Today:" in line:
            capitals.append((current_date, line.split("Starting Capital Today: ")[1].strip()))

    for i in range(len(capitals)):
        start_cap = capitals[i][1]
        end_cap = capitals[i+1][1] if i + 1 < len(capitals) else ""
        if end_cap == "":
            for line in reversed(lines):
                 if "Final Capital:" in line:
                     end_cap = line.split("Final Capital: ")[1].strip()
                     break

        start_val = float(start_cap.replace('₹', ''))
        end_val = float(end_cap.replace('₹', ''))

        diff = end_val - start_val

        print(f"{capitals[i][0][5:]}\t{start_cap}\t{'+₹' if diff >=0 else '-₹'}{abs(diff):.2f}\t{end_cap}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_log(sys.argv[1])
