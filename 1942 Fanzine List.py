from bs4 import BeautifulSoup
import requests
import collections
import Helpers

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

    # The line is a list of tags and strings. Ignore the strings
    for tag2 in line:
        if tag2.string != None:
            continue

        # Now we have a single fanzine entry. It has the format <li><a...></li>. We want the <a...> part
        # This is the first member of the tag's contents list.
        a=tag2.contents[0]
        hrefLinkText, hrefUrl=Helpers.GetHrefAndTextFromTag(a)
        listOf1942s[hrefLinkText.lower()]=(hrefLinkText, hrefUrl)

del tag, tag2, hrefUrl, hrefLinkText, a, s, table

# Now we have a dictionary containing the names and URLs of the 1942 fanzines.
# The next step is to figure out what 1942 issues of each we have on the website
# We do this by reading the fanzines/<name>/index.html file and then decoding the table in it.

# Loop over the list of fanzines
for (key, (title, relPath)) in listOf1942s.items():

    # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
    # We need to turn relPath into a URL
    url=Helpers.RelPathToURL(relPath)
    print(title, "", url)

    # Download the index.html which lists all of the issues of the specified currently on the site
    h = requests.get(url)

    s = BeautifulSoup(h.content, "html.parser")
    b = s.body.contents
    # Because the structures of the pages are so random, we need to search the body for the table.
    # *So far* all of the tables have been headed by <table border="1" cellpadding="5">, so we look for that.

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

    # Some of the items showing up in val.contents will be strings containing newlines -- start by compressing them out.
    val.contents=Helpers.RemoveNewlineRows(val.contents)

    # Ok. We have the table.  Make a list of the column headers. We need to compress the newlines out of this as well
    tableHeader = Helpers.RemoveNewlineRows(val.contents[0])
    columnHeaders = []
    for col in tableHeader:
        columnHeaders.append(col.string)

    # Next, we select just the rows for 1942
    # Note that the dates aren't especially consistent, either, so we have to do some searching
    # What column contains the year?
    yearCol=Helpers.FindIndexOfStringInList(columnHeaders, "Year")
    issueCol=Helpers.FindIndexOfStringInList(columnHeaders, "Issue")
    titleCol=Helpers.FindIndexOfStringInList(columnHeaders, "Title")
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
        tableRow=Helpers.RemoveNewlineRows(val.contents[i])
        row=[]
        for j in range(0, len(tableRow)-1):
            if (j != issueCol):
                row.append(tableRow[j].string)
            else:
                row.append(Helpers.GetHrefAndTextFromTag(tableRow[j]))

        rows.append(row)


    # Now select just the fanzines for 1942
    for row in rows:
        if row[yearCol] == "1942":
            print(row[issueCol][1])

del yearCol, issueCol, titleCol, row, i, tableRow, columnHeaders, tableHeader, col, key, title, relPath, s, h, j, b
print("---Starting read of 1942 Fanzine List.txt")

# Define a named tuple to hold the data I get from Joe's input file
JoesData=collections.namedtuple("JoesData", "Name Editor Stuff")

# OK, next we open the complete list of 1942 fanzines from Joe Siclari.
# Each line follows a vague pattern:
# <title> '(' <name of editor(s) ')' <a usually comma-separated list of issues> <crap, frequently in parenthesis>
# Store the parsed information in a list of tuples
f=open("1942 All Fanzines List.txt")
allFanzines1942=[]
for line in f:  # Each line is a fanzine
    if line[-1:] == "\n":   # Drop the trailing newline
        line=line[:-1]
    temp="".join(line.split())  # This is a Python idiom which removes whitespace from a string
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

    allFanzines1942.append(JoesData(line[:loc1-1], line[loc1+1:loc2].title(), line[loc2+1:]))

f.close()
del f, line, temp, loc1, loc2
print("---fanzines1942 list created with "+str(len(allFanzines1942))+" elements")


print("--- Read Links1942.txt")
# Now we read Links1942.txt, which contains links to issues of fanzines *outside* fanac.org.
# It's organized as a table, with the first row a ';'-delimited list of column headers
#    and the remaining rows are each a ';'-delimited pointer to an exteral fanzine

# First read the header line which names the columns.  The headers are separated from ';", so we need to remove these.
f=open("Links1942.txt")
line=f.readline()
line=line.replace(";", "")
links1942ColNames=line.split(" ")

# Define a named tuple to hold the data I get from the external links input file
# This -- elegantly -- defines a named tuple to hold the elements of a line and names each element according to the column header in the first row.
ExternalLinksData=collections.namedtuple("ExternalLinksData", line)

# Now read the rest of the data.
externalLinks1942=[]
for line in f:  # Each line after the first is a link to an external fanzine

    temp=line.split(";")
    t2=[]
    for t in temp:
        t2.append(t.strip())
    externalLinks1942.append(ExternalLinksData(*tuple(t2))) # Turn the list into a named tuple.

f.close()
del f, line, t2, t, temp
print("--- Completed reading Links1942.txt")

# Now we go through the list we just parsed and generate the output document.
#   1. We link the fanzine name to the fanzine page on fanac.org
#   2. We link each issue number to the individual issue
#   3. We highlight those fanzines which are eligible for a 1942 Hugo

# Define a named tuple to hold the expanded data I get by combining all the sources
ExpandedData=collections.namedtuple("ExpandedData", "Name Editor Stuff IsHugoEligible NameOnFanac URL Issues")

for i in range(0, len(allFanzines1942)):
    fanzine=allFanzines1942[i]

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
        for ex in externalLinks1942:
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
    allFanzines1942[i]=ExpandedData(fanzine[0], fanzine[1], fanzine[2], isHugoEligible, name, Helpers.RelPathToURL(url), None)

del fanzine, ex, jname, name, url, i, isHugoEligible

print("----Begin reading Fanac fanzine directory formats.txt")
# Next we read the table of fanac.org file formats.
# Fanac.org's fanzines are *mostly* in one format, but there are at least a dozen different ways of presenting them.
# The table will allow us to pick the right method for reading the index.html file and locating the right issue URL
try:
    f=open("Fanac fanzine directory formats.txt", "r")
except:
    print("Can't open 'Fanac fanzine directory formats.txt'")

# Read the file.  Lines beginning with a # are comments and are ignored
# Date lines consist of a commz-separated list:
#       The first two elements are code numbers
#       The remaining elements are directories in fanac.org/fanzines
#       We create a dictionary of fanzine directory names in lower case.
#       The value of each directory entry is a tuple consisting of Name (full case) folowed by the two numbers.
fanacFanzineDirectoryFormats={}
for line in f:
    line=line.strip()   # Make sure there are no leading or traling blanks
    if len(line) == 0 or line[0] == "#":    # Ignore some lines
        continue
    # We apparently have a data line. Split it into tokens. Remove leading and traling blanks, but not internal blanks.
    spl=line.split(",")
    if len(spl) < 3:    # There has to be at least three tokens (the two numbers and at least one directory name)
        print("***Something's wrong with "+line)
        continue
    nums=spl[:2]
    spl=spl[2:]
    for dir in spl:
        fanacFanzineDirectoryFormats[dir.lower()]=(nums[0], nums[1], dir)

del line, spl, nums, dir
print("----Done reading Fanac fanzine directory formats.txt")

# OK, now the problem is to decode the crap at the end to form a list of issue numbers...or something...
# We'll start by trying to recognize *just* the case where we have a comma-separated list of numbers and nothing else.
for i in range(0, len(allFanzines1942)):
    fz=allFanzines1942[i]

    if fz.Stuff == None:       # Skip empty stuff
        continue
    stuff="".join(fz.Stuff.split()) # Compress out whitespace
    if len(stuff) == 0:     # Skip if it's allwhitespace
        continue
    spl=stuff.split(",")
    if len(spl) == 0:       # Probably can't happen
        continue

    # OK, spl is now a list of one or more comma-separated items from Stuff
    # See if they're all numbers
    isInt=True
    for s in spl:
        try:
            int(s)
        except:
            isInt=False
            break

    if not isInt:
        print("Not all integers: "+str(spl))

# ... more to do here!

del isInt, s, spl, i, stuff



print("---Generate the HTML")
f=open("1942.html", "w")
f.write("<body>\n")
f.write("<ul>\n")

# Create the HTML file
for fz in allFanzines1942:
    print(fz)

    htm=None
    if fz.IsHugoEligible:
        name=fz.Name.title()    # Joe has eligible name all in UC.   Make them normal title case.
        if name != None and fz.URL != None:
            # We have full information for an eligible zine
            str="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+name+"</a>"
            htm='<font color="#FF0000">Eligible</font>&nbsp;&nbsp;<i><a href="'+fz.URL+'">'+name+"</a></i>"+" ("+fz.Editor+") "+fz.Stuff
        elif name != None and fz.URL == None:
            # We're missing a URL for an eligible zine
            str="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff
            htm='<font color="#FF0000">Eligible</font>&nbsp;&nbsp;<i>'+name+"</i>"+" ("+fz.Editor+") "+fz.Stuff
        else:
            # We're missing all information from fanac.org for an eligible fanzine -- it isn't there
            str=name+" ("+fz.Editor+") "+fz.Stuff
            htm='<font color="#FF0000">Eligible</font>&nbsp;&nbsp;<i>'+fz.Name+"</i> ("+fz.Editor+") "+fz.Stuff
    else:
        if fz.Name != None and fz.URL != None:
            # We have full information for an ineligible zine
            str=fz.Name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+fz.Name+"</a>"
            htm='<i><a href="'+fz.URL+'">'+fz.Name+"</a></i>"+" ("+fz.Editor+") "+fz.Stuff
        elif fz.Name != None and fz.URL == None:
            # We're missing a URL for an ineligible item
            str=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+"</a></i>"+" ("+fz.Editor+") "+fz.Stuff
        else:
            # We're missing all information from fanac.org for an ineligible fanzine -- it isn't there
            str=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+"</i> ("+fz.Editor+") "+fz.Stuff

    print(str)
    if htm != None:
        f.write("<li><p>\n")
        f.write(htm+"</li>\n")

f.write("</ul></body>")
f.flush()
f.close()

f2=open("1942 Fanzines Not on fanac.txt", "w")
f2.write("1942 Fanzines not on fanac.org\n\n")
for fz in allFanzines1942:
    if fz.NameOnFanac == None or fz.URL == None:
        f2.write(fz.Name+"\n")
f2.flush()
f2.close()
del f2, htm, str, fz


i=0