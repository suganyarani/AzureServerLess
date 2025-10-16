import sys

def main(arg):
    print(arg)
    with open("testdata/genai-testdata.jsonl", "r") as infile, open(arg, "w") as outfile:
        for line in infile:
            outfile.write(line)
    print("success")

if __name__ == "__main__":
    print("HELLO WORLD")
    print("Starting script...")
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("No argument provided.")