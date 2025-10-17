import os
import sys

def main(arg):   
    try: 
        with open("testdata/genai-testdata.jsonl", "r") as infile, open(arg, "w") as outfile:
            for line in infile:
                outfile.write(line)
        
        result = "success"  # do your computation here
        # Write a step output for GitHub Actions
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            print(f"result={result}", file=f)

    except Exception as e:
        print("failed")
        print(e)
if __name__ == "__main__":
    print("hello world")
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("failed")