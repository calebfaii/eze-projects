"""
This module accomplishes the following:

    1. Make a call to JIRA API using specified JIRA ticket
    2. Extract key fields from this ticket
    3. Make another call to the JIRA API to obtain the ML merge FV
    4. Generate the HF announcement
"""

from jira import JIRA
from flask import Flask, render_template
import webbrowser
import secrets

class jiraSession(object):

    user = secrets.user
    pw = secrets.pw
    options = {'server': 'https://jira.ezesoft.net'}
    session = None
    hfJiraID = None
    approver = None
    hotfix = None
    mainline = None

    def __init__(self, hfJiraID, approver):

        self.hfJiraID = hfJiraID
        self.approver = approver
        self.connectToJira()

    def makeIssue(self):

        return jiraIssue()

    def connectToJira(self):

        self.session = JIRA(basic_auth=(self.user, self.pw), options=self.options)

    def setHotfix(self, jiraIssue):

        self.hotfix = jiraIssue

    def setMainline(self, jiraIssue):

        self.mainline = jiraIssue

    def generateContent(self):

        hotfixJiraObject = self.makeIssue()
        hotfixJiraObject.populateBasic(self, self.hfJiraID)
        hotfixJiraObject.populateAll(self)
        self.setHotfix(hotfixJiraObject)

        mainlineJiraObject = self.makeIssue()
        mainlineJiraObject.populateBasic(self, str(hotfixJiraObject.mainlineIssue))
        self.setMainline(mainlineJiraObject)

    def getMLCaseStatus(self):

        if self.mainline.status == 'Closed':
            return "This issue has been resolved in the head version in %s with " % self.mainline.fixVersion
        else:
            return "This issue will be resolved in the head version (%s) in " % self.mainline.fixVersion

    def getApprover(self):

        return self.approver

    def generateAnnouncement(self):

        announcementContent = {'approvalInfo': "Hotfix approved by %s. %s." % (self.getApprover(), self.hotfix.summary),
                               'mainlineInfo': self.getMLCaseStatus(),
                               'mainlineLink': self.mainline.sourceLink,
                               'mainlineID' : self.mainline.sourceID,
                               'client': self.hotfix.client,
                               'clientLink': self.hotfix.clientLink,
                               'dateIn': self.hotfix.dateIn,
                               'sourceID': self.hotfix.sourceID,
                               'sourceLink': self.hotfix.sourceLink,
                               'sfCaseNum': self.hotfix.salesforceCaseNumber,
                               'sfCaseLink': self.hotfix.salesforceCaseLink,
                               'category': self.hotfix.category,
                               'version': self.hotfix.fixVersion}

        return announcementContent


class jiraIssue(object):

    jiraObject = None
    summary = None
    fixVersion = None
    dateIn = None
    sourceID = None
    sourceLink = None
    salesforceCaseNumber = None
    salesforceCaseLink = None
    category = None
    client = None
    clientLink = None
    status = None
    mainlineIssue = None

    def populateBasic(self, jiraSession, jiraIssue):

        self.jiraObject = jiraSession.session.issue(jiraIssue)
        self.summary = self.jiraObject.fields.summary
        self.fixVersion = self.jiraObject.fields.fixVersions[0]
        self.sourceID = jiraIssue
        self.sourceLink = '%s/browse/%s' % (jiraSession.options['server'], self.sourceID)
        self.status = str(self.jiraObject.raw['fields']['status']['name'])

    def populateAll(self, jiraSession):

        self.dateIn = self.formatDate()
        self.setSFCaseAndLink()
        self.setCategory()
        self.setClientNameAndLink()
        self.findMLCase(jiraSession)

    def formatDate(self):

        rawDate = self.jiraObject.raw['fields']['customfield_14563']
        year = rawDate[0:4]
        month = rawDate[5:7]
        day = rawDate[8:]
        return "%s/%s/%s" % (month, day, year)

    def formatSFLink(self, link):

        return 'https://ezesoft.my.salesforce.com/%s' % link

    def getSFCaseNum(self):

        try:
            caseNum = self.jiraObject.raw['fields']['customfield_11561']
        except Exception:
            caseNum = "-"
        return caseNum

    def getSFCaseLink(self):

        try:
            caseLink = self.formatSFLink(self.jiraObject.raw['fields']['customfield_12863'][0])
        except Exception:
            caseLink = None
        return caseLink

    def setSFCaseAndLink(self):

        self.salesforceCaseNumber = self.getSFCaseNum()
        self.salesforceCaseLink = self.getSFCaseLink()

    def getClientName(self):

        try:
            clientName = self.jiraObject.raw['fields']['customfield_12969']
        except Exception:
            clientName = 'None'
        return clientName

    def getClientLink(self):

        try:
            clientLink = self.formatSFLink(self.jiraObject.raw['fields']['customfield_12861'][0])
        except Exception:
            clientLink = None
        return clientLink

    def setClientNameAndLink(self):

        self.client = self.getClientName()
        self.clientLink = self.getClientLink()

    def setCategory(self): # TODO: fix

        subcategory = None

        try:
            category = self.jiraObject.raw['fields']['customfield_12860']['value']
        except Exception:
            category = None

        if category:
            try:
                subcategory = self.jiraObject.raw['fields']['customfield_12860']['child']['value']
            except Exception:
                subcategory = None

        if category:
            if subcategory:
                self.category = '%s - %s' % (category, subcategory)
                return
            self.category = category

    def findMLCase(self, jiraSession):

        issueLinks = self.jiraObject.raw['fields']['issuelinks']
        for issue in issueLinks:
            try:
                key = issue['inwardIssue']['key']
            except Exception:
                key = issue['outwardIssue']['key']
            jiraIssue = jiraSession.session.issue(key)
            issueSummary = jiraIssue.fields.summary
            if issueSummary[0:4] == 'MAIN':
                if key[0:3] != 'CRS' and key[0:3] != 'DOC':
                    self.mainlineIssue = key
        return

hfjira = raw_input("Hotfix JIRA ID: ")
ap = raw_input("Approver's last name: ")
app = Flask(__name__)
@app.route('/')
def go(hfjira=hfjira, ap=ap):
    session = jiraSession(hfjira, ap)
    session.generateContent()
    content = session.generateAnnouncement()
    # webbrowser.open("http://localhost:5000/", new=1, autoraise=True)
    return render_template('index.html',**content)

if __name__ == "__main__":
    app.run()
