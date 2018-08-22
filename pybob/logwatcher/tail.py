"""Simple file watcher."""
import time
import sys


def watch(fn):
    fp = open(fn, 'r')
    fp.seek(0, 2)
    while True:
        new = fp.readline()
        # Once all lines are read this just returns ''
        # until the file changes and a new line appears

        if new:
            yield new
        else:
            time.sleep(0.5)


def main():
    fn = sys.argv[1]
    for line in watch(fn):
        print(line.rstrip())

if __name__ == "__main__":
    sys.exit(main())

