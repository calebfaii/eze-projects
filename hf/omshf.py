from jira import JIRA
from flask import Flask, render_template
import termcolor
import webbrowser
import secrets


class Printer(object):

    def pPrint(self, protocol, data):

        if protocol == 'E':
            self.printError(data)

        if protocol == 'S':
            self.printSuccess(data)

    @staticmethod
    def printError(data):

        color = 'red'
        attributes = ['bold']
        print termcolor.colored(data, color=color, attrs=attributes)

    @staticmethod
    def printSuccess(data):
        color = 'green'
        attributes = ['bold']
        print termcolor.colored(data, color=color, attrs=attributes)


class JiraSession(object):

    user = secrets.user
    pw = secrets.pw
    options = {'server': 'https://jira.ezesoft.net'}
    hotfixJiraIDs = None
    JIRAObject = None
    hotfixApprover = None
    hfJiraID = None
    hotfixJiraIssueObjects = []
    mainlineJiraID = None
    mainlineJiraIssueObject = None
    hotfixSummary = None
    __printer = Printer()

    def __init__(self, hotfixJiraIDList):

        self.hotfixJiraIDs = hotfixJiraIDList
        self.connectToJira()

    @staticmethod
    def makeIssue(jiraID):

        return JiraIssue(jiraID)

    def connectToJira(self):

        try:
            self.JIRAObject = JIRA(basic_auth=(self.user, self.pw), options=self.options)
            self.__printer.pPrint('S', 'JIRA connection successful.')
        except Exception, e:
            self.__printer.pPrint('E', 'JIRA connection failed: %s' % e)
            raise StandardError

    def populateHotfixObjectList(self, jiraIssueObject):

        self.hotfixJiraIssueObjects.append(jiraIssueObject)

    def findMLIssueKeyInIssueLinks(self, jiraIssueObject):

        issueLinks = jiraIssueObject.raw['fields']['issuelinks']
        for issue in issueLinks:
            try:
                key = issue['inwardIssue']['key']
            except Exception, e:
                self.__printer.pPrint("E", "Inward issue link not found: %s" % e)
                self.__printer.pPrint("E", "Locating outward issues...")
                key = issue['outwardIssue']['key']
                if key:
                    self.__printer.pPrint("S", 'Mainline issue located.')
                else:
                    self.__printer.pPrint("S", 'Mainline issue not found.')
            jiraIssue = self.JIRAObject.issue(key)
            issueSummary = jiraIssue.fields.summary
            if issueSummary[0:4] == 'MAIN':
                if key[0:3] != 'CRS' and key[0:3] != 'DOC':
                    return key
        return None

    def setMainlineJiraID(self, jiraIssueID):

        if not self.mainlineJiraID:
            self.mainlineJiraID = str(jiraIssueID)

    def setMainlineIssueObject(self, jiraIssueObject):

        if not self.mainlineJiraIssueObject:
            self.mainlineJiraIssueObject = jiraIssueObject

    def getJiraProjectKeyFromJira(self):

        jiraIssueObject = self.hotfixJiraIssueObjects[0]
        return jiraIssueObject.jiraObject.raw['fields']['project']['key']

    def getProjectLeadFromJira(self):

        projectName = self.getJiraProjectKeyFromJira()
        projectObject = self.JIRAObject.project(projectName)
        return projectObject.lead.displayName

    def setJiraApproverNameFromJira(self):

        approverFullName = [str(word) for word in self.getProjectLeadFromJira().split(" ")]
        approverLastName = approverFullName[-1]
        self.hotfixApprover = approverLastName

    def generateContent(self):

        hotfixJiraObjects = []
        for i in self.hotfixJiraIDs:
            issueObj = self.makeIssue(i)
            hotfixJiraObjects.append(issueObj)
        for issue in hotfixJiraObjects:
            issue.populateJiraFieldAttributes(self)
            issue.populateSalesforceFieldAttributes()
            mainlineIssueKey = self.findMLIssueKeyInIssueLinks(issue.jiraObject)
            self.setMainlineJiraID(mainlineIssueKey)
        for i in hotfixJiraObjects:
            self.populateHotfixObjectList(i)

        mainlineJiraObject = self.makeIssue(self.mainlineJiraID)
        mainlineJiraObject.populateJiraFieldAttributes(self)
        self.setMainlineIssueObject(mainlineJiraObject)
        self.setJiraApproverNameFromJira()
        self.setHotfixSummary()

    def getMLCaseStatus(self):

        if self.mainlineJiraIssueObject.status == 'Closed':
            return "This issue has been resolved in the head version in %s with " % \
                   self.mainlineJiraIssueObject.fixVersion
        else:
            return "This issue will be resolved in the head version (%s) in " % \
                   self.mainlineJiraIssueObject.fixVersion

    def setHotfixSummary(self):

        summary = self.hotfixJiraIssueObjects[0].summary
        if summary[0:2] == 'SR':
            firstHyphen = summary.find("-") + 2
            if firstHyphen:
                self.hotfixSummary = summary[firstHyphen:]
                return
        else:
            self.hotfixSummary = summary

    def generateIssueDict(self, jiraIssueObject):

        issueDict = {'clientInfo': {'clientName': jiraIssueObject.client,
                                    'clientLink': jiraIssueObject.clientLink},
                     'dateIn': jiraIssueObject.dateIn,
                     'sourceInfo': {'sourceID': jiraIssueObject.sourceID,
                                    'sourceLink': jiraIssueObject.sourceLink},
                     'sfInfo': {'sfCaseNum': jiraIssueObject.salesforceCaseNumber,
                                'sfCaseLink': jiraIssueObject.salesforceCaseLink},
                     'category': jiraIssueObject.category,
                     'version': jiraIssueObject.fixVersion}
        return issueDict

    def generateAllIssueDictList(self):

        dictList = []
        for issue in self.hotfixJiraIssueObjects:
            key = issue.sourceID
            value = self.generateIssueDict(issue)
            dictList.append({key: value})
        return dictList

    def generateAnnouncement(self):

        dictList = self.generateAllIssueDictList()
        announcementContent = {'emailSubject': 'HOTFIX ANNOUNCEMENT: %s' % self.hotfixSummary,
                               'approvalInfo': "Hotfix approved by %s. %s." %
                                               (self.hotfixApprover,
                                                self.hotfixSummary),
                               'mainlineInfo': self.getMLCaseStatus(),
                               'mainlineLink': self.mainlineJiraIssueObject.sourceLink,
                               'mainlineID': self.mainlineJiraIssueObject.sourceID,
                               'hotfixes': dictList}
        return announcementContent


class JiraIssue(object):

    __printer = Printer()
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

    def __init__(self, jiraID):

        self.sourceID = jiraID

    def populateJiraFieldAttributes(self, jiraSession):

        self.jiraObject = jiraSession.JIRAObject.issue(self.sourceID)
        self.summary = self.jiraObject.fields.summary
        self.fixVersion = str(self.jiraObject.fields.fixVersions[0])
        self.sourceLink = '%s/browse/%s' % (jiraSession.options['server'], self.sourceID)
        self.status = str(self.jiraObject.raw['fields']['status']['name'])

    def populateSalesforceFieldAttributes(self):

        self.dateIn = self.formatDate()
        self.populateSalesforceCaseAndLink()
        self.populateCategory()
        self.populateClientNameAndLink()

    def formatDate(self):

        rawDate = self.jiraObject.raw['fields']['customfield_14563']
        year = rawDate[0:4]
        month = rawDate[5:7]
        day = rawDate[8:]
        return "%s/%s/%s" % (month, day, year)

    @staticmethod
    def formatSFLink(link):

        return 'https://ezesoft.my.salesforce.com/%s' % link

    def getSFCaseNumFromJira(self):

        try:
            caseNum = self.jiraObject.raw['fields']['customfield_11561']
        except Exception, e:
            self.__printer.pPrint("E", "Salesforce case number not found: %s" % e)
            caseNum = "-"
        return caseNum

    def getSFCaseLinkFromJira(self):

        try:
            caseLink = self.formatSFLink(self.jiraObject.raw['fields']['customfield_12863'][0])
        except Exception, e:
            self.__printer.pPrint("E", "Salesforce case link not found: %s" % e)
            caseLink = None
        return caseLink

    def populateSalesforceCaseAndLink(self):

        self.salesforceCaseNumber = self.getSFCaseNumFromJira()
        self.salesforceCaseLink = self.getSFCaseLinkFromJira()

    def getClientNameFromJira(self):

        try:
            clientName = self.jiraObject.raw['fields']['customfield_12969']
        except Exception, e:
            self.__printer.pPrint("E", "Client name not found: %s" % e)
            clientName = 'None'
        return clientName

    def getClientLinkFromJira(self):

        try:
            clientLink = self.formatSFLink(self.jiraObject.raw['fields']['customfield_12861'][0])
        except Exception, e:
            self.__printer.pPrint("E", "Client link not found: %s" % e)
            clientLink = None
        return clientLink

    def populateClientNameAndLink(self):

        self.client = self.getClientNameFromJira()
        self.clientLink = self.getClientLinkFromJira()

    def populateCategory(self):

        # TODO: investigate this method with some more use cases.

        subcategory = None

        try:
            category = self.jiraObject.raw['fields']['customfield_12860']['value']
        except Exception, e:
            self.__printer.pPrint("E", "Category not found: %s" % e)
            category = None

        if category:
            try:
                subcategory = self.jiraObject.raw['fields']['customfield_12860']['child']['value']
            except Exception, e:
                self.__printer.pPrint("E", "Subcategory not found: %s" % e)
                subcategory = None

        if category:
            if subcategory:
                self.category = '%s - %s' % (category, subcategory)
                return
            self.category = category

hotfixJiraIDs = []
while True:
    hfJiraID = raw_input("Hotfix JIRA ID: ")
    if hfJiraID:
        hotfixJiraIDs.append(hfJiraID)
    if not hfJiraID:
        break

# session = JiraSession(hotfixJiraIDs)
# session.generateContent()
# cont = session.generateAnnouncement()
# print "OK"

app = Flask(__name__)

@app.route('/')
def go(hotfixJiraIDList=hotfixJiraIDs):
    session = JiraSession(hotfixJiraIDs)
    session.generateContent()
    content = session.generateAnnouncement()
    return render_template('index.html', **content)
webbrowser.open("localhost:5000/", new=1, autoraise=True)
if __name__ == "__main__":
    app.run()

# CREATE A DICT OF 'KEYS' - EACH KEY IS A HF ID, THE VALUE IS THE CONTENT DICT
# PASS THE KEYS TO THE APP BY CREATING A METHOD