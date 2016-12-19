from jira import JIRA
import json
import urllib
import secrets

link = secrets.website
username = secrets.username
pw = secrets.password


def connectJira(jira_server, jira_user, jira_password):
    """"
    Connect to JIRA. Return None on error
    """
    try:
        print "Connecting to JIRA: %s" % jira_server
        jira_options = {'server': jira_server}
        jira = JIRA(options=jira_options,
                    basic_auth=(jira_user,
                                jira_password))
        print "JIRA connection successful."
        print " "
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
        print " "
        return lace_epics
    except Exception, e:
        print "Failed to retrieve Epics: %s" % e
        return None

lace_epics = getLaceEpics()
jira = connectJira(link, username, pw)
issues_in_version = jira.search_issues("fixVersion='5.7 SR10.12.0'", fields='Epic Link', maxResults=500)
# parsed_issues = json.loads(issues_in_version.read())
# for issue in parsed_issues:
    # print issue
