from jira import JIRA
import secrets

link = secrets.website
username = secrets.username
pw = secrets.password

def connect_jira(jira_server, jira_user, jira_password):
    '''
    Connect to JIRA. Return None on error
    '''
    try:
        print "Connecting to JIRA: %s" % jira_server
        jira_options = {'server': jira_server}
        jira = JIRA(options=jira_options,
                    basic_auth=(jira_user,
                                jira_password))
        return jira
    except Exception,e:
        print "Failed to connect to JIRA: %s" % e
        return None

jira = connect_jira(link, username, pw)
issues_in_proj = jira.search_issues('project=OPI')
for issue in issues_in_proj:
    print issue
