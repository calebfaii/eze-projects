"""
This module implements a series of tools to connect to SharePoint .ASPX
pages, parse content, and prepare this content for migration to Confluence.

Users must be on the Eze network to access SharePoint or Confluence.

The sole objective of this module is to extract, transform, and store the following
page attributes:

    - Page title
    - Page content
    - Page images
    - Page attachments

Ultimately, a collection of "page" objects will be returned to the user for disposition
as desired.
"""

from bs4 import BeautifulSoup
import requests
import lxml
from requests_ntlm import HttpNtlmAuth
from httplib import responses
import wikisecrets
import re
# TODO: REPLACE THIS WITH GETPASS WHEN READY

# GLOBAL PARAMETERS:
SHAREPOINT_USERNAME = wikisecrets.wiki_user
SHAREPOINT_PASSWORD = wikisecrets.wiki_pw
SHAREPOINT_HOSTNAME = "http://sp2013web01:1818"
SP_HOST_HOMEPAGE = "/sites/wikis/fixwiki/Pages/Welcome_to_the_FIX_Wiki.aspx/_api/"
SP_HOME_URL = SHAREPOINT_HOSTNAME + SP_HOST_HOMEPAGE

VALID_SEARCH_PATH = '/sites/wikis/fixwiki/Pages/'


def connection_successful(response_code):

    """
    Custom exception helper function for handling HTTP Response Code errors.

    Any response code other than 200 will trigger a 'Warning' exception, which
    can be handled, or not handled, depending on the instance.
    """

    if response_code == 200:
        return True
    else:
        raise Warning('Connection failed. Response code %d: "%s"' % (response_code, responses[response_code]))


def sharepoint_session(sharepoint_user=SHAREPOINT_USERNAME,
                       sharepoint_pw=SHAREPOINT_PASSWORD,
                       domain=SP_HOME_URL):

    """
    This function authenticates a SharePoint session and returns a
    Session object.

    The arguments are a SharePoint username, password, and domain.  In
    this case, the "domain" refers to the home page of the wiki.

    This session object can maintain authentication for as long as
    required, and can be used to submit arbitrary POST requests.

    Default values can be modified at the top of this module.
    """

    session = requests.Session()
    authenticate = session.post(domain,
                                auth=HttpNtlmAuth(sharepoint_user,
                                                  sharepoint_pw))
    HTTP_response_code = authenticate.status_code
    if connection_successful(HTTP_response_code):
        print "SharePoint connection successful."
        return session


def get_page_HTML(active_session, page_link):

    """
    Returns the HTML of a SharePoint wiki page as a giant string.

    An active session object
    and a page link are provided as parameters. Default values can be
    modified at the top of this module.

    The two local variables at the beginning of this function must be
    added manually.  They form useful brackets on the wiki page
    content that we're looking for.  I found them by examining a few
    pages in Developer Tools and finding some common class types. Basically,
    these strings are used to define the start and end points of the
    HTML snippets we want.
    """

    content_start = '<div class="edit-mode-border">'
    content_end = '<div class="right-wp-zone-col">'

    page_object = active_session.post(page_link)
    if connection_successful(page_object.status_code):
        page_html = page_object.content[(page_object.text.find(content_start)
                                         + len(content_start)):page_object.text.find(content_end)]
        return page_html


## TODO: BOT - CRAWL PAGES FOR VALID SITES
def get_page_resources(page_html):
    """
    This bot returns a list of all valid links found in a given page.

    The 'href' attribute of the HTML is parsed.  Links for other links,
    photos, and attachments are returned.
    """

    soup = BeautifulSoup(page_html, "lxml")
    return [link.get('href')for link in soup.findAll('a')]


def return_web_links(page_soup, valid_link_path=VALID_SEARCH_PATH):

    """
    Returns a list of valid web links found on a page.
    """

    web_links = []

    try:
        for line in page_soup:
            if line.startswith(valid_link_path):
                if line.endswith('.aspx'):
                    web_links.append(line)
        return web_links

    except:
        return False


# MESSY, BUT THIS CRAWLS ALL PAGES
counter = 1
testsesh = sharepoint_session()
starting = get_page_resources(get_page_HTML(testsesh, page_link=SP_HOME_URL))
pages_to_go = []

p = return_web_links(starting)
for a in p:
    if a not in pages_to_go:
        pages_to_go.append(a)
for i in pages_to_go:
    link = SHAREPOINT_HOSTNAME + i
    try:
        ht = get_page_HTML(testsesh, link)
    except:
        continue
    rr = get_page_resources(ht)
    for i in rr:
        print i
    mm = return_web_links(rr)
    if mm:
        for i in mm:
            if i not in pages_to_go:
                pages_to_go.append(i)
    counter += 1
print "###################################"
print "Total pages crawled: ", counter
print "Total valid web pages found: ", len(pages_to_go)
print "Valid links: "
for i in pages_to_go:
    print i

######################################################################

def create_page_file():
    """This function creates a file folder based on the name of a page.

    This is a helper function which creates a named archive folder for
    a given SharePoint page, which is provided as a parameter.

    This structure allows us to preserve the images from a given page,
    serving as a 'golden copy' of the page's image content.
    """
    pass

def save_to_file():
    """
    This function saves files to disk.  The target save location,
    web file location, and file name are provided as parameters.

    Name validation is performed before saving."""

    # re.search("\\/?%*:|\<>'", str)
    # use this for images and attachments
    pass


## TODO: FUNCTION - EFFICIENTLY PARSE AND STORE ALL SITE, IMAGE, AND ATTACHMENT LINKS
def crawl_all_pages():
    pass



## TODO: HANDLE TABLE FORMATTING
