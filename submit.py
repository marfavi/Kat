import os, requests, sys, re, json, time
from get import promptToGet
from programSelector import formatProgramFile, selectProgramFile, guessLanguage
from config import getConfig, getUrl, formatUrl
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Kat"}


def submit(args, options):
    problemName = args[0]
    directory = os.path.join(os.getcwd(), problemName)

    if not os.path.exists(problemName):
        promptToGet(args, options)
        return

    # if programFile is not given, we will attempt to guess it
    programFile = (
        formatProgramFile(args[1]) if args[1:] else selectProgramFile(problemName)
    )

    if programFile == -1:
        return

    config = getConfig()

    session = requests.Session()

    login(config, session)

    print("Submitting...")

    id = postSubmission(config, session, problemName, programFile)

    print("Submission successfull (id "+id+")")

    if id == -1:
        return

    results = []
    isRunning = True
    testTotal = 0
    while isRunning:
        login(config, session)
        newResults, testTotal = watchUntilCompleted(id, session, config)
        for i in range(0, abs(len(newResults) - len(results))):
            sys.stdout.write("\U0001F49A")
        sys.stdout.flush()
        if(testTotal != 0 and len(newResults) == int(testTotal)):
            isRunning = False
            break
        results = newResults
        time.sleep(1)
    print()
    print("🎉 Congratulations! You completed all " + testTotal + " tests for " + problemName)


def login(config, session):
    username = config.get("user", "username")
    token = config.get("user", "token")
    login_url = getUrl(config, "loginurl", "login")

    session.post(login_url, data={
        "user": username, "token": token, "script": "true"
    }, headers=_HEADERS)


def postSubmission(config, session, problemName, programFile):
    url = getUrl(config, "submissionurl", "submit")
    language = guessLanguage(programFile)
    if language == -1:
        print("Could not guess language for " + programFile)
        return -1

    data = {
        "submit": "true",
        "submit_ctr": 2,
        "language": formatLanguage(language),
        # "mainclass": mainclass,
        "problem": problemName,
        "script": "true",
    }

    sub_files = []
    with open(programFile['relativePath']) as sub_file:
        sub_files.append((
            "sub_file[]",
            (programFile['name'], sub_file.read(), "application/octet-stream"),
        ))
    

    response = session.post(
        url, data=data, files=sub_files, headers=_HEADERS
    )

    body = response.content.decode('utf-8').replace('<br />', '\n')
    match = re.search(r'Submission ID: ([0-9]+)', body)

    if match is None:
        print("Submission was received, but could not read ID from response. Visit the submission manually in the browser.")
        print("Response was: "+body)
        return -1

    return match.group(1).strip()


def formatLanguage(language):
    if(language == "Python"):
        return formatPythonLanguage(language)
    
    return language

def formatPythonLanguage(language):
    python_version = str(sys.version_info[0])

    if python_version not in ['2', '3']:
        print('python-version in .kattisrc must be 2 or 3')
        sys.exit(1)
    
    return 'Python ' + python_version

def watchUntilCompleted(id, session, cfg):
    response = session.get(
        "https://open.kattis.com/submissions/"+id, headers=_HEADERS
    )

    body = response.content.decode('utf-8')
    soup = BeautifulSoup(body, 'html.parser')
    [info, testcases] = soup.select("#judge_table tbody tr")
    
    results = []

    testTotal = 0

    for testcase in testcases.select(".testcases > span"):
        testResult = testcase.get('title')
        match = re.search(r"Test case (\d+)\/(\d+): (.+)", testResult)
        testNumber = match.group(1)
        testTotal = match.group(2)
        testStatus = match.group(3)
        if(testStatus == "Wrong Answer"):
            print("\U0000274C\nWrong answer on " + testNumber + " of " + testTotal)
            sys.exit(1)
        elif testStatus == "not checked":
            break

        results.append(testStatus)

    return results, testTotal