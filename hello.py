import sys

def main(arg):
    print(arg)

if __name__ == "__main__":
    print("HELLO WORLD")
    print("Starting script...")
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("No argument provided.")