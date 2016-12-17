from jira import JIRA
from collections import Counter

link = 'https://stgjira.ezesoft.net/'
username = 'cfall'
pw = ''

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
print issues_in_proj
