import requests
from lxml import html
from requests_ntlm import HttpNtlmAuth

import wikisecrets

# USER: ezesoft\\name

session = requests.Session()
main_page = session.post("http://sp2013web01:1818/sites/wikis/fixwiki/Pages/Welcome_to_the_FIX_Wiki.aspx/_api/",
                         auth=HttpNtlmAuth(wikisecrets.wiki_user, wikisecrets.wiki_pw))

tree = html.fromstring(main_page.content)
rootmenu = tree.xpath('//*[@id="zz8_RootAspMenu"]/*/*/*/span[@class="menu-item-text"]/text()')
rootlinks = tree.xpath('//*[@id="zz8_RootAspMenu"]/*/a/@href')

for item in rootmenu:
    if item.startswith('-'):
        rootmenu.remove(item)

host_link = 'http://sp2013web01:1818'
pages = {rootmenu[index]: rootlinks[index] for index in xrange(0, 32)}

content_start = '<div class="edit-mode-border">'
content_end = '<div class="right-wp-zone-col">'

test_page = session.post(host_link + pages["FX"])
print test_page.content
# print test_page.content[(test_page.text.find(content_start) + len(content_start)):test_page.text.find(content_end)]






