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

s=BeautifulSoup(h.content, "html.parser")
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

    #-------------------------------------
    # Inline definition of a function to pull and hfref and accompanying text from a Tag
    # The structure is "<a href='URL'>LINKTEXT</a>
    # We want to extract the URL and LINKTEXT
    def GetHrefAndTextFromTag(tag):
        try:
            href=tag.contents[0].attrs["href"]
        except:
            try:
                href=tag.attrs["href"]
            except:
                href=None
        return (tag.contents[0].string, href)
    # -------------------------------------

    # The line is a list of tags and strings. Ignore the strings
    for tag2 in line:
        if tag2.string != None:
            continue

        # Now we have a single fanzine entry. It has the format <li><a...></li>. We want the <a...> part
        # This is the first member of the tag's contents list.
        a=tag2.contents[0]
        hrefLinkText, hrefUrl=GetHrefAndTextFromTag(a)
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
    # Inline definition of a function to search recursively for the table containing the fanzines listing
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
    # Inline definition of a function to compress newline elements from a list of Tags.
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
    tableHeader = RemoveNewlineRows(val.contents[0])
    columnHeaders = []
    for col in tableHeader:
        columnHeaders.append(col.string)

    #---------------------------------------
    # Inline definition of a function to find the index of a string in a list of strings
    def FindIndexOfStringInList(list, str):
        for i in range(0, len(list) - 1):
            if list[i] == str:
                return i
    #---------------------------------------

    # Next, we select just the rows for 1942
    # Note that the dates aren't especially consistsnt, either, so we have to do some searching
    # What column contains the year?
    yearCol=FindIndexOfStringInList(columnHeaders, "Year")
    issueCol=FindIndexOfStringInList(columnHeaders, "Issue")
    titleCol=FindIndexOfStringInList(columnHeaders, "Title")
    if issueCol == None:
        issueCol=titleCol

    # If there's no yearCol or issueCol, just print a message and go on to the next fanzine
    if yearCol == None:
        print("    No yearCol found")
        continue
    if issueCol == None:
        print("    No issueCol found")
        continue

    # What's left is one or more rows, each corresponding to an issue of that fanzine.
    # We build up a list of lists.  Each list in the list of lists is a row
    # We have to treat the Title colum specially, since it contains the critical href we need.
    rows=[]
    for i in range(1, len(val)):
        tableRow=RemoveNewlineRows(val.contents[i])
        row=[]
        for j in range(0, len(tableRow)-1):
            if (j != issueCol):
                row.append(tableRow[j].string)
            else:
                row.append(GetHrefAndTextFromTag(tableRow[j]))

        rows.append(row)


    # Now select just the fanzines for 1942
    for row in rows:
        if row[yearCol] == "1942":
            print(row[issueCol][1])

    i=0


i=0