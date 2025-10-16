import sys

def main(arg):   
    try: 
        with open("testdata/genai-testdata.jsonl", "r") as infile, open(arg, "w") as outfile:
            for line in infile:
                outfile.write(line)
        print("success")
    except Exception as e:
        print("failed")
        print(e)
if __name__ == "__main__":    
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("failed")