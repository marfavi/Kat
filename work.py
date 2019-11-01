from archive import archive
from get import get
from list import collectProblems
from submit import submit
from test import test


def workCommand(args, options):
    problems = [x[0] for x in collectProblems(args, [])]
    currentI = 0
    currentProblem = getProblem(currentI, options, problems)
    while True:
        command = input()
        if command == "exit":
            break
        elif command == "test":
            test([currentProblem], [])
        elif command == "submit":
            submitOptions = [x for x in ["archive"] if x in options]
            successful = submit([currentProblem], submitOptions)
            if successful:
                currentI += 1
                currentProblem = getProblem(currentI, options, problems)
        elif command == "skip":
            archive([currentProblem], [])
            currentI += 1
            currentProblem = getProblem(currentI, options, problems)


def getProblem(currentI, options, problems):
    currentProblem = problems[currentI]
    getOptions = [x for x in ["open"] if x in options]
    get([currentProblem], getOptions)
    return currentProblem