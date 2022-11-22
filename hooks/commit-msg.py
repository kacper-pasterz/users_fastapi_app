#!/usr/bin/env python
import sys
import re


reqRegex = "^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(([\w\-\.]+))?(!)?: ([\w ])+([\s\S]*)"


commitMessageFile = open(sys.argv[1])
commitMessage = commitMessageFile.read().strip()


if re.search(reqRegex, commitMessage):
    print("Valid commit message")
    sys.exit(0)
else:
    print("Invalid commit message")
    sys.exit(1)

