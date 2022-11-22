import sys
import re
from git import Repo


def main():
    repo = Repo('.')
    branch_name = repo.active_branch.name
    reqRegex = "^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(([\w\-\.]+))?(!)?: ([\w ])+([\s\S]*)"
    commitMessageFile = open(sys.argv[1])
    commitMessage = commitMessageFile.read().strip()

    if re.search("(major|feature|bugfix|hotfix)/*", branch_name):
        print('Correct branch name given')

        if re.search(reqRegex, commitMessage):
            print("Valid commit message")
            sys.exit(0)
        else:
            print("Invalid commit message")
            sys.exit(1)
    else:
        print('Wrong branch name given')
        sys.exit(1)


if __name__ == '__main__':
    main()
