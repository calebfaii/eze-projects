import json
import urllib

from jira import JIRA

from hf import secrets

link = secrets.website
username = secrets.username
pw = secrets.password

print " "
print "Welcome to Epic Checker."
print ' '
print "_-_-_-_-_-_-_-_-_-_-_-_-_-_"
print ' '


def connectJira(jira_server, jira_user, jira_password):
    """"
    Connect to JIRA. Return None on error
    """
    try:
        print "Connecting to JIRA: %s" % jira_server
        print " "
        jira_options = {'server': jira_server}
        jira = JIRA(options=jira_options,
                    basic_auth=(jira_user,
                                jira_password))
        print "JIRA connection successful."
        print ' '
        print "_-_-_-_-_-_-_-_-_-_-_-_-_-_"
        print ' '
        return jira
    except Exception, e:
        print "Failed to connect to JIRA: %s" % e
        return None


def getLaceEpics():
    """"
    Connect to LACE.  Return Epics, Team, and Jira Key.  Return None on error.
    """
    lace_epics = []
    url = "https://lace.ezesoft.net/api/releases/reports/product-team/100"
    try:
        print "Retrieving Epics from LACE..."
        print ' '
        response = urllib.urlopen(url)
        root = json.loads(response.read())
        prod = root["Products"]
        for product in prod:
            for team in product['Teams']:
                for epic in team['Epics']:
                    epicname = str(epic['name'])
                    teamname = str(team['name'])
                    jirakey = str(epic['jiraKey'])
                    epic_team_jira = (epicname, teamname, jirakey)
                    lace_epics.append(epic_team_jira)
        print "Epics returned successfully."
        print ' '
        print "_-_-_-_-_-_-_-_-_-_-_-_-_-_"
        print ' '
        return lace_epics
    except Exception, e:
        print "Failed to retrieve Epics: %s" % e
        return None

def getJiraEpics():
    """"
    Connect to JIRA.  Return unique list of Epic Names in  and Jira Key.  Return None on error.
    """
    jira_epics = []
    jira_epic_names = []
    jira = connectJira(link, username, pw)
    print "Performing lookup..."
    print " "
    print "[*   ]"
    issues_in_version = jira.search_issues("fixVersion='5.7 SR10.12.0' AND type != Epic",
                                           maxResults=500)
    print "[**  ]"
    for issue in issues_in_version:
        epiclink = issue.fields.customfield_10860
        if epiclink not in jira_epics and type(epiclink) != None:
            jira_epics.append(epiclink)
    print "[*** ]"
    for epic in jira_epics:
        try:
            e = jira.issue(epic)
            ep = e.fields.summary
            epic_key = (ep, epic)
            jira_epic_names.append(epic_key)
        except:
            continue
    print "[****]"
    return jira_epic_names

lace_epics = getLaceEpics()
jepics = getJiraEpics()

lace_keys = []
for epic in lace_epics:
    lkey = epic[2]
    lace_keys.append(lkey)

print " "
print "UNLINKED EPICS:"
print "_______________"
print " "
for jepic in jepics:
    ekey = jepic[1]
    if ekey not in lace_keys:
        print "Epic: ", str(jepic[0])
        print "Key: ", str(jepic[1])
        print " "
print "< End of list. >"
