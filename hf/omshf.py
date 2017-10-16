from jira import JIRA
from flask import Flask, render_template
import termcolor
import webbrowser
import secrets

# class Printer(object):
#
#     def printError(self, data):
#
#         color = 'red'
#         attributes = ['bold']
#         print termcolor.colored(data, color=color, attrs=attributes)
#
#     def printSuccess(self, data):
#         color = 'green'
#         attributes = ['bold']
#         print termcolor.colored(data, color=color, attrs=attributes)

class jiraSession(object):

    user = secrets.user
    pw = secrets.pw
    options = {'server': 'https://jira.ezesoft.net'}
    session = None
    hfJiraID = None
    hotfix = None
    mainline = None

    def __init__(self, hfJiraID):

        self.hfJiraID = hfJiraID
        self.connectToJira()

    def printError(self, data):

        color = 'red'
        attributes = ['bold']
        print termcolor.colored(data, color=color, attrs=attributes)

    def printSuccess(self, data):
        color = 'green'
        attributes = ['bold']
        print termcolor.colored(data, color=color, attrs=attributes)

    def makeIssue(self):

        return jiraIssue()

    def connectToJira(self):

        try:
            self.session = JIRA(basic_auth=(self.user, self.pw), options=self.options)
            self.printSuccess('JIRA connection successful.')
        except Exception, e:
            self.printError('JIRA connection failed: %s' % e)
            raise StandardError

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

    def createEmailSubject(self):

        summary = self.hotfix.summary
        if summary[0:2] == 'SR':
            firstHyphen = summary.find("-") + 2
            if firstHyphen:
                return summary[firstHyphen:]
        else:
            return summary

    def generateAnnouncement(self):

        announcementContent = {'emailSubject': 'HOTFIX ANNOUNCEMENT: %s' % self.createEmailSubject(),
                               'approvalInfo': "Hotfix approved by %s. %s." %
                                               (self.hotfix.approver,
                                                self.hotfix.summary),
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
    approver = None

    def printError(self, data):

        color = 'red'
        print termcolor.colored(data, color=color)

    def printSuccess(self, data):

        color = 'green'
        attributes = ['bold']
        print termcolor.colored(data, color=color, attrs=attributes)

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
        self.setApprover(jiraSession)

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
        except Exception, e:
            self.printError("Salesforce case number not found: %s" % e)
            caseNum = "-"
        return caseNum

    def getSFCaseLink(self):

        try:
            caseLink = self.formatSFLink(self.jiraObject.raw['fields']['customfield_12863'][0])
        except Exception, e:
            self.printError("Salesforce case link not found: %s" % e)
            caseLink = None
        return caseLink

    def setSFCaseAndLink(self):

        self.salesforceCaseNumber = self.getSFCaseNum()
        self.salesforceCaseLink = self.getSFCaseLink()

    def getClientName(self):

        try:
            clientName = self.jiraObject.raw['fields']['customfield_12969']
        except Exception, e:
            self.printError("Client name not found: %s" % e)
            clientName = 'None'
        return clientName

    def getClientLink(self):

        try:
            clientLink = self.formatSFLink(self.jiraObject.raw['fields']['customfield_12861'][0])
        except Exception, e:
            self.printError("Client link not found: %s" % e)
            clientLink = None
        return clientLink

    def setClientNameAndLink(self):

        self.client = self.getClientName()
        self.clientLink = self.getClientLink()

    def setCategory(self):

        # TODO: investigate this method with some more use cases.

        subcategory = None

        try:
            category = self.jiraObject.raw['fields']['customfield_12860']['value']
        except Exception, e:
            self.printError("Category not found: %s" % e)
            category = None

        if category:
            try:
                subcategory = self.jiraObject.raw['fields']['customfield_12860']['child']['value']
            except Exception, e:
                self.printError("Subcategory not found: %s" % e)
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
            except Exception, e:
                self.printError("Inward issue link not found: %s" % e)
                self.printError("Locating outward issues...")
                key = issue['outwardIssue']['key']
                if key:
                    self.printSuccess('Mainline issue located.')
                else:
                    self.printError('Mainline issue not found.')
            jiraIssue = jiraSession.session.issue(key)
            issueSummary = jiraIssue.fields.summary
            if issueSummary[0:4] == 'MAIN':
                if key[0:3] != 'CRS' and key[0:3] != 'DOC':
                    self.mainlineIssue = key
        return

    def getJiraProjectKey(self):

        return self.jiraObject.raw['fields']['project']['key']

    def getProjectLead(self, jiraSession):

        projectName = self.getJiraProjectKey()
        projectObject = jiraSession.session.project(projectName)
        return projectObject.lead.displayName

    def getJiraApproverName(self, jiraSession):

        approverFullName = [str(word) for word in self.getProjectLead(jiraSession).split(" ")]
        approverLastName = approverFullName[-1]
        return approverLastName

    def setApprover(self, jiraSession):

        self.approver = self.getJiraApproverName(jiraSession)

hfJiraID = raw_input("Hotfix JIRA ID: ")
app = Flask(__name__)
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.FATAL)
@app.route('/')
def go(hfJiraID=hfJiraID):
    session = jiraSession(hfJiraID)
    session.generateContent()
    content = session.generateAnnouncement()
    return render_template('index.html',**content)
webbrowser.open("localhost:5000/", new=1, autoraise=True)
if __name__ == "__main__":
    app.run()

# TODO: Disposition to clipboard
# TODO: Test cases
