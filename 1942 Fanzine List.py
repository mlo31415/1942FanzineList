from bs4 import BeautifulSoup
from bs4 import NavigableString
import requests
import os
import collections

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
print("---Retro_Hugos.html downloaded")

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
            href=tag.contents[0].attrs.get("href", None)
        except:
            href=tag.attrs.get("href")

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
        listOf1942s[hrefLinkText.lower()]=(hrefLinkText, hrefUrl)

# Now we have a dictionary containing the names and URLs of the 1942 fanzines.
# The next step is to figure out what 1942 issues of each we have on the website
# We do this by reading the fanzines/<name>/index.html file and then decoding the table in it.

#-----------------------------------------
# Inline defintion of function to generate the proper kind of path.  (This may change depending on the target location of the output.)
def RelPathToURL(relPath):
    if relPath == None:
        return "<no path>"
    if relPath[0] == ".":
        return "http://www.fanac.org/"+os.path.normpath(os.path.join("fanzines", relPath)).replace("\\", "/")
    return relPath
#-----------------------------------------

# Loop over the list of fanzines
for (key, (title, relPath)) in listOf1942s.items():

    # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
    # We need to turn relPath into a URL
    url=RelPathToURL(relPath)
    print(title, "", url)

    # Download the index.html which lists all of the issues of the specified currently on the site
    h = requests.get(url)

    s = BeautifulSoup(h.content, "html.parser")
    b = s.body.contents
    # Because the structures of the pages are so random, we need to search the body for the table.
    # *So far* all of the tables have been headed by <table border="1" cellpadding="5">, so we look for that.

    #-----------------------------------------
    # Define inline a simple function to name tags for debugging purposes
    def N(tag):
        try:
            return tag.__class__.__name__
        except:
            return "Something"
    #-----------------------------------------

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
    # Note that the dates aren't especially consistent, either, so we have to do some searching
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

print("---Starting read of 1942 Fanzine List.txt")

# Define a named tuple to hold the data I get from Joe's input file
JoesData=collections.namedtuple("JoesData", "Name Editor Stuff")

# OK, next we open the complete list of 1942 fanzines from Joe Siclari.
# Each line follows a vague pattern:
# <title> '(' <name of editor(s) ')' <a usually comma-separated list of issues> <crap, frequently in parenthesis>
# Store the parsed information in a list of tuples
f=open("1942 Fanzine List.txt")
fanzines1942=[]
for line in f:  # Each line is a fanzine
    if line[-1:] == "\n":
        line=line[:-1]
    temp="".join(line.split())
    if len(temp) == 0:  # Ignore lines that are all whitespace
        continue

    loc1=line.find("(")
    if loc1 == -1:
        print("*** Could find opening '(' in '"+ line + "'")
        continue

    loc2=line.find(")", loc1)
    if loc2 == -1:
        print("*** Could find closing ')' in '"+ line + "'")
        continue

    fanzines1942.append(JoesData(line[:loc1-1], line[loc1+1:loc2].title(), line[loc2+1:]))

f.close()
print("---fanzines1942 list created with "+str(len(fanzines1942))+" elements")


print("--- Read Links1942.txt")
# Now we read Links1942.txt, which contains links to issues of fanzines *outside* fanac.org.
# It's organized as a table, with the first row a ';'-delimited list of column headers
#    and the remaining rows are each a ';'-delimited pointer to an exteral fanzine

# Firdst read the neader line which names the columns
f=open("Links1942.txt")
line=f.readline()
line=line.replace(";", "")
links1942ColNames=line.split(" ")

# Define a named tuple to hold the data I get from the external links input file
ExternalLinksData=collections.namedtuple("ExternalLinksData", line)

# Now read the rest of the data.
links1942=[]
for line in f:  # Each line after the first is a link to an external fanzine

    temp=line.split(";")
    t2=[]
    for t in temp:
        t2.append(t.strip())
    links1942.append(ExternalLinksData(*tuple(t2)))

f.close()
print("--- Completed reading Links1942.txt")

# Now we go through the list we just parsed and generate the output document.
#   1. We link the fanzine name to the fanzine page on fanac.org
#   2. We link each issue number to the individual issue
#   3. We highlight those fanzines which are eligible for a 1942 Hugo

# Define a named tuple to hold the expanded data I get by combining all the sources
ExpandedData=collections.namedtuple("ExpandedData", "Name Editor Stuff isHugoEligible, Name2, URL")

for i in range(0, len(fanzines1942)):
    fanzine=fanzines1942[i]

    # First we take the fanzine name from Joe's 1942 Fanzine List.txt and match it to a 1942 fanzine on fanac.org
    jname=fanzine[0]

    isHugoEligible=False        # Joe has tagged Hugo-eligible fanzines by making their name to be all-caps
    if jname == jname.upper():
        isHugoEligible=True

    # listOf1942s is a dictionary of 1942 fanzines that we have on fanac.org. The key is the fanzine name in lower case
    # the value is a tuple of the fanzine name and the URL on fanac.org
    # We want to look up the entries from Joe's list and see if they are on it.
    name=None
    url=None
    if jname.lower() in listOf1942s:
        name, url=listOf1942s[jname.lower()]
        print("   Found (1): "+name +" --> " + url)
    else:
        # Try adding a trailing ", the"since sometimes Joe's list omits this
        if (jname.lower()+", the") in listOf1942s:
            name, url = listOf1942s[jname.lower()+", the"]
            print("   Found (2): " + name + " --> " + url)
        else:
            print("   Not found: "+jname)

    # If that didn't work, see if we have a match in the list of external links
    if name == None:
        for ex in links1942:
            if jname.lower() == ex.Title.lower():
                name, url = (ex.Title, ex.URL)
                print("   Found (3): " + name + " --> " + url)
                break
            else:
                # Try adding a trailing ", the"since sometimes Joe's list omits this
                if (jname.lower() + ", the") == ex.Title.lower():
                    name, url =  (ex.Title, ex.URL)
                    print("   Found (4): " + name + " --> " + url)
                    break
    if name == None:
        print("   Not found (5): " + jname)

    # Update the 1942 fanzines list with the new information
    fanzines1942[i]=ExpandedData(fanzine[0], fanzine[1], fanzine[2], isHugoEligible, name, RelPathToURL(url))

    # OK, now the problem is to decode the crap at the end to form a list of issue numbers...or something...
    # ***Skipped for the present***

print("---Generate the HTML")
f=open("1942.html", "w")
f.write("<body>\n")
f.write("<ul>\n")
# Create the HTML file
for fz in fanzines1942:
    print(fz)

    htm=None
    if fz.isHugoEligible:
        name=fz.Name.title()    # Joe has eligible name all in UC.   Make them normal title case.
        if fz.Name2 != None:
            name2=fz.Name2.title()
        if name2 != None and fz.URL != None:
            # We have full information for an eligible zine
            str="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+name2+"</a>"
            htm='<font color="#FF0000">Eligible</font>&nbsp;&nbsp;<i><a href="'+fz.URL+'">'+name2+"</a></i>"+" ("+fz.Editor+") "+fz.Stuff
        elif name2 != None and fz.URL == None:
            # We're missing a URL for an eligible zine
            str="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff
            htm='<font color="#FF0000">Eligible</font>&nbsp;&nbsp;<i><a href="'+fz.URL+'"></i>'+name2+"</a>"+" ("+fz.Editor+") "+fz.Stuff
        elif name2 == None:
            # We're missing all information from fanac.org for an eligible fanzine -- it isn't there
            str=name+" ("+fz.Editor+") "+fz.Stuff+"   MISSING from fanac.org"
            htm='<font color="#FF0000">Eligible</font>&nbsp;&nbsp;<i>'+fz.Name+"</i> ("+fz.Editor+") "+fz.Stuff+"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(MISSING from fanac.org)"
    else:
        if fz.Name2 != None and fz.URL != None:
            # We have full information for an ineligible zine
            str=fz.Name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+fz.Name2+"</a>"
            htm='<i><a href="'+fz.URL+'">'+fz.Name2+"</a></i>"+" ("+fz.Editor+") "+fz.Stuff
        elif fz.Name2 != None and fz.URL == None:
            # We're missing a URL for an ineligible item
            str=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i><a href="'+fz.URL+'">&nbsp;&nbsp;'+fz.Name2+"</a></i>"+" ("+fz.Editor+") "+fz.Stuff
        elif fz.Name2 == None:
            # We're missing all infromation from fanac.org for an ineligible fanzine -- it isn't there
            str=fz.Name+" ("+fz.Editor+") "+fz.Stuff+"   MISSING from fanac.org"
            htm='<i>'+fz.Name+"</i> ("+fz.Editor+") "+fz.Stuff+"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(MISSING from fanac.org)"

    print(str)
    if htm != None:
        f.write("<li><p>\n")
        f.write(htm+"</li>\n")

f.write("</ul></body>")
f.close()


i=0