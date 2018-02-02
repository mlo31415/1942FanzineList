from bs4 import BeautifulSoup
from bs4 import NavigableString
import requests
import os

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
table=s.body.ol.contents

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
# The next step is to figure out what 1942 issues of each we have on the website
# We do this by reading the fanzines/<name>/index.html file and then decoding the table in it.

# Loop over the list of fanzines
for title, relPath in listOf1942s.items():

    # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
    # We need to turn relPath into a URL
    url="http://www.fanac.org/"+os.path.normpath(os.path.join("fanzines", relPath)).replace("\\", "/")
    print (title, "", url)

    # Download the index.html which lists all of the issues of the specified currently on the site
    h = requests.get(url)

    s = BeautifulSoup(h.content, "html.parser")
    b = s.body.contents
    # Because the structures of the pages are so random, we need to search the body for the table.
    # *So far* all of the tables have been headed by <table border="1" cellpadding="5">, so we look for that.
    def N(tag):
        try:
            return tag.__class__.__name__
        except:
            return "Something"


    # ----------------------------------------
    # Define inline a function to search recursively for the table containing the fanzines listing
    def LookForTable(tag):
        #print("call LookForTable with tag=", N(tag))
        for stuff in tag:
            #print ("   stuff=", stuff.name)
            if stuff.name == "table":
                #print("   Table found!!!")
                # Next, we check the table to see if it has the values table border="1" cellpadding="5"
                try:
                    if stuff.attrs["border"] == "1" and stuff.attrs["cellpadding"] == "5":
                        return stuff
                except:
                    continue
            try:
                if len(stuff.contents) > 0:
                    val=LookForTable(stuff.contents)
                if val != None:
                    #print("   val popped")
                    return val
            except:
                continue
        #print("   Return None")
        return None
    #----------------------------------------

    # And now use it.
    val=LookForTable(b)
    if val == None:
        print("*** No Table found!")
        continue

    # OK, we probably have the issue table.  Now decode it.
    # The first row is the column headers
    # Subsequent rows are fanzine issue rows

    #----------------------------------------
    # Define inline a function to compress newline elements from a list of Tags.
    def RemoveNewlineRows(tags):
        compressedTags = []
        for row in tags:
            if not isinstance(row, NavigableString):
                compressedTags.append(row)
        return compressedTags
    #----------------------------------------

    # Some of the items showing up in val.contents will be strings containing newlines -- start by compressing them out.
    val.contents=RemoveNewlineRows(val.contents)

    # Ok. We have the table.  Make a list of the column headers. We need to compress the newlines out of this as well
    tableHeader=RemoveNewlineRows(val.contents[0])
    columnHeaders=[]
    for col in tableHeader:
        columnHeaders.append(col.string)
    i=0


i=0