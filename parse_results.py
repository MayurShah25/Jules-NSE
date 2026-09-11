import sys

def parse_log(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "BACKTEST SUMMARY" in line:
            print("="*50)
            for j in range(1, 5):
                if i+j < len(lines):
                    print(lines[i+j].strip())
            print("="*50)

if __name__ == "__main__":
    parse_log(sys.argv[1])
