from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import FanacOrgReaders
import RetroHugoReaders


# Create the list of FanacName tuples which will be used by FanacName functions
FanacOrgReaders.ReadClassicModernPages()

# Read Joe's PDF and create a list of tuples, each representing one of the complete set of fanzines of 1942
# The three items of the tuple is the fanzine name, the fanzine editors, andf the fanzine issue data.
# Some of this is pretty rough, being taken from somewhat inconsistant text in the PDF.
# This will also add any new names found to the FanacNames tuples
allFanzines1942=RetroHugoReaders.Read1942FanzineList()

# A list of all 1942 fanzines with issue information
listOf1942FanzinesOnFanac=RetroHugoReaders.ReadRetro_HugosTxtFile()

# A dictionary of fanzine directory formats
fanacFanzineDirectoryFormats=FanacOrgReaders.ReadFanacOrgFormatsTxt()

# A dictionary of links of individual issues to external websites
externalLinks1942=RetroHugoReaders.ReadLinks1942Txt()


#============================================================================================
# Read index.html files on fanac.org
# We have a dictionary containing the names and URLs of the 1942 fanzines.
# The next step is to figure out what 1942 issues of each we have on the website
# We do this by reading the fanzines/<name>/index.html file and then decoding the table in it.
# What we get out of this is a list of fanzines with name, URL, and issue info.

# Loop over the list of all 1942 fanzines, building up a list of those on fanac.org
print("----Begin reading index.html files on fanac.org")
fanacIssueInfo=[]
for (key, (title, relPath)) in listOf1942FanzinesOnFanac.items():

    # Get the index file format for this directory
    try:
        dn=FanacNames.DirName(title.lower())
        fmt=fanacFanzineDirectoryFormats[dn.lower()]
        print("   Format: "+title + " --> "+FanacNames.StandardizeName(title.lower()) + " --> " + str(fmt))
    except:
        print("   Format: "+title + " --> "+FanacNames.StandardizeName(title.lower()) + " -->  (0, 0)")
        # This is actually a good thing, because it means that the fanzines has the default index.html type
        print("   fanacFanzineDirectoryFormats["+title.lower()+"] not found")
        # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
        # We need to turn relPath into a URL
        url=Helpers.RelPathToURL(relPath)
        print(title, " ", url)
        ret=FanacOrgReaders.ReadFanacFanzineIndexPage(title, url, (0,0, None), fanacIssueInfo)
        if ret != None:
            fanacIssueInfo=ret
        continue

    # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
    # We need to turn relPath into a URL
    url=Helpers.RelPathToURL(relPath)
    print(title, " ", url)
    ret=FanacOrgReaders.ReadFanacFanzineIndexPage(title, url, fmt, fanacIssueInfo)
    if ret != None:
        fanacIssueInfo=ret

del url, key, title, relPath, ret
# Now we have a list of all the issues of fanzines onfanac.org which have at least one 1942 issue.(Not all of the issues are 1942.)
print("----Done reading index.html files on fanac.org")



#============================================================================================
print("----Begin combining information into one table.")
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
    if jname.lower() in listOf1942FanzinesOnFanac:
        name, url=listOf1942FanzinesOnFanac[jname.lower()]
        print("   Found (1): "+name +" --> " + url)
    else:
        # Try adding a trailing ", the"since sometimes Joe's list omits this
        if (jname.lower()+", the") in listOf1942FanzinesOnFanac:
            name, url = listOf1942FanzinesOnFanac[jname.lower()+", the"]
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
print("----Done combining information into one table.")


#============================================================================================
print("----Begin decoding issue list in list of all 1942 fanzines")
# Define a named tuple to hold the an issue number
IssueNumber=collections.namedtuple("IssueNumber", "Vol Num")

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
    # See if they're all interpretable as issue numbers
    listOfIssues=[]     # A list of issue tuples
    isReasonable=True
    for s in spl:
        iss=IssueNumber(*Helpers.DecodeIssueDesignation(s))
        if iss.Num == None:
            isReasonable=False
            break
        listOfIssues.append(iss)

    allFanzines1942[i]=ExpandedData(fz.Name, fz.Editor, fz.Stuff, fz.IsHugoEligible, fz.NameOnFanac, fz.URL, listOfIssues)
    if not isReasonable:
        print("Not all interpretable: "+str(spl))

del isReasonable, s, spl, i, stuff, listOfIssues, iss
print("----Done decoding issue list in list of all 1942 fanzines")


#============================================================================================
# Next we do the arduous business of looking at fanac.org and finding the URLs that go with each issue
# For each fanzine, we need to:
#       Given the fanzine name, find its directory name
#       Get the directory's index.html file
#       Look up the type of index.html file we have
#       If it's one we know how to interpret, we:
#           Go down the list of issue designators
#           Look up the URL for that issue in the index.html file
#           Add the URL to the issue designator
for i in range(0, len(allFanzines1942)):
    fz=allFanzines1942[i]
    name=fz.NameOnFanac


#============================================================================================
print("----Begin generating the HTML")
f=open("1942.html", "w")
f.write("<body>\n")
f.write('<table border="0" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 0; margin-bottom: 0">\n<tr>\n<td valign="top" align="left">')
f.write("<ul>\n")

# Create the HTML file
linecount=0
for fz in allFanzines1942:
    print(fz)

    #-------------------------------------
    # Inline function to format Stuff
    # Stuff is commonly a list of issue specification interspersed with nonce items
    # For now, we'll attempt only to format what we interpret, above: whole numbers and Vol/# combinations
    def FormatStuff(fz):
        ex=fz.Issues
        if ex == None or len(ex) == 0:
            return fz.Stuff
        out=""
        for issue in ex:
            # issue is a tuple of a vol and a num.
            # If both exists, it is a Vn#n pair
            # If V is none, then num is a whole number.
            # Neither existing should never happen
            if issue[0] == None and issue[1] == None:
                v="(oops) "+ fz.Stuff

            elif issue[0] == None:
                v= str(issue[1])

            else:
                v="V"+str(issue[0])+"#"+str(issue[1])

            if len(out) > 0:
                out=out+", "
            out=out+v
        return out
    #-----------------------

    htm=None
    if fz.IsHugoEligible:
        name=fz.Name.title()    # Joe has eligible name all in UC.   Make them normal title case.
        if name != None and fz.URL != None:
            # We have full information for an eligible zine
            txt="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+name+"</a>"
            htm='<i><a href="'+fz.URL+'">'+name+'</a></i>&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp;'+" ("+fz.Editor+") <br>"+FormatStuff(fz)
        elif name != None and fz.URL == None:
            # We're missing a URL for an eligible zine
            txt="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+name+"</i>"+'&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp; ('+fz.Editor+") <br>"+FormatStuff(fz)
        else:
            # We're missing all information from fanac.org for an eligible fanzine -- it isn't there
            txt=name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+'</i>&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp; ('+fz.Editor+") <br>"+FormatStuff(fz)
    else:
        if fz.Name != None and fz.URL != None:
            # We have full information for an ineligible zine
            txt=fz.Name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+fz.Name+"</a>"
            htm='<i><a href="'+fz.URL+'">'+fz.Name+"</a></i>"+" ("+fz.Editor+") <br>"+FormatStuff(fz)
        elif fz.Name != None and fz.URL == None:
            # We're missing a URL for an ineligible item
            txt=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+"</a></i>"+" ("+fz.Editor+") <br>"+FormatStuff(fz)
        else:
            # We're missing all information from fanac.org for an ineligible fanzine -- it isn't there
            txt=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+"</i> ("+fz.Editor+") <br>"+FormatStuff(fz)
    linecount=linecount+1
    if linecount == len(allFanzines1942)/2:
        f.write('</td>\n<td valign="top" align="left">\n<ul>')

    print(txt)
    if htm != None:
        f.write('<li><p>\n')
        f.write(htm+'</li>\n')

f.write('</td>\n</tr>\n</table>')
f.write('</ul></body>')
f.flush()
f.close()

f2=open("1942 Fanzines Not on fanac.txt", "w")
f2.write("1942 Fanzines not on fanac.org\n\n")
for fz in allFanzines1942:
    if fz.NameOnFanac == None or fz.URL == None:
        f2.write(fz.Name+"\n")
f2.flush()
f2.close()
del f2, htm, txt, fz

print("----Done generating the HTML")


i=0