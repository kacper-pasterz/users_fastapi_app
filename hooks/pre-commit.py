#!/usr/bin/python
import sys
import re
from git import Repo


def main():
    repo = Repo(".")
    name = repo.active_branch.name
    if re.search("(major|feature|bugfix|hotfix)/*", name):
        print("Correct branch name given")
        sys.exit(0)
    else:
        print("Wrong branch name given")
        sys.exit(1)


if __name__ == '__main__':
    main()

