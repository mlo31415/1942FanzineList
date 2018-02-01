from bs4 import BeautifulSoup
import requests

# Find text bracketed by <b>...</b>
# Return the contents of the first pair of brackets found and the remainder of the input string
def FindBracketedText(s, b):
    strlower=s.lower()
    l1=strlower.find("<"+b.lower())
    if l1 == -1:
        return "", ""
    l1=strlower.find(">", l1)
    if l1 == -1:
        print("***Error: no terminating '>' found in "+strlower+"'")
        return "", ""
    l2=strlower.find("</"+b.lower()+">", l1+1)
    if l2 == -1:
        return "", ""
    return s[l1+1:l2], s[l2+3+len(b):]

# Download the fanac.org webpage which lists all of the 1942 fanzine issues currently on the site
h=requests.get("http://www.fanac.org/fanzines/Retro_Hugos.html")

s=BeautifulSoup(h.content)
b=s.body
table=b.ol.contents

# The structure of the table is
#       A string "\n"
#       A <li> tag containing the editor's name
#       A <ul> tag containing one or more lines of fanzines
#       A <br/> tag
# All we care about is the <ul> tag, which we need to decode to find individual fanzines.
# Loop over the tags to find entries
listOf1942s = dict()
for tag in table:
    if tag.name != "ul":
        continue
    line=tag.contents

    # The line is a list of tags and strings. Ignore the strings
    for tag2 in line:
        if tag2.string != None:
            continue

        # Now we have a single fanzine entry. It has the format <li><a...></li>. We want the <a...> part
        # This is the first member of the tag's contents list.
        a=tag2.contents[0]

        # Now we have a hyperlink. The structure is "<a href='URL'>LINKTEXT</a>
        # We want to extract the URL and LINKTEXT
        hrefUrl=a.attrs["href"]
        hrefLinkText=a.contents[0]
        listOf1942s[hrefLinkText]=hrefUrl

# Now we have a dictionary containing the names and URLs of the 1942 fanzines.
    # The next step is to figure out what 1942 issues of each we have on the websoite


i=0