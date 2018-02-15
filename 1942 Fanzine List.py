from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import FanacOrgReaders
import RetroHugoReaders

# Create the list of FanacName tuples which will be used by FanacName functions
# Note: This is just to get the names and directories, nothing else.
FanacOrgReaders.ReadClassicModernPages()
FanacNames.AddFanacDirectories(FanacOrgReaders.g_FanacDirectories)

# Read Joe's PDF and create a list of tuples, each representing one of the complete set of fanzines of 1942
# The three items of the tuple are the fanzine name, the fanzine editors, andf the fanzine issue data.
# Some of this is pretty rough, being taken from somewhat inconsistant text in the PDF.
# This will also add any new names found to the FanacNames tuples
allFanzines1942=RetroHugoReaders.Read1942FanzineList()

# A dictionary of links of individual issues to external websites
global externalLinks1942
externalLinks1942=RetroHugoReaders.ReadLinks1942Txt()

# Read the fanac.org fanzine direcgtory and produce a lost of all issues present
FanacOrgReaders.ReadFanacFanzineIssues(FanacOrgReaders.g_FanacDirectories)


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
    jname=fanzine.Name

    isHugoEligible=False        # Joe has tagged Hugo-eligible fanzines by making their name to be all-caps
    if jname == jname.upper():
        isHugoEligible=True

    # listOf1942s is a dictionary of 1942 fanzines that we have on fanac.org. The key is the fanzine name in lower case
    # the value is a tuple of the fanzine name and the URL on fanac.org
    # We want to look up the entries from Joe's list and see if they are on it.
    name=None
    url=None
    if FanacOrgReaders.g_FanacDirectories.Contains(jname.lower()):
        name, url=FanacOrgReaders.g_FanacDirectories.GetTuple(jname.lower())
        print("   Found (1): "+name +" --> " + url)

    # Try adding a trailing ", the"since sometimes Joe's list omits this
    elif FanacOrgReaders.g_FanacDirectories.Contains(jname.lower()+", the"):
        name, url = FanacOrgReaders.g_FanacDirectories.GetTuple(jname.lower()+", the")
        print("   Found (2 -- add ', the'): " + name + " --> " + url)

    # Try compressing blanks out
    elif FanacOrgReaders.g_FanacDirectories.Contains(jname.lower().replace(" ", "")):
        name, url=FanacOrgReaders.g_FanacDirectories.GetTuple(jname.lower().replace(" ", ""))
        print("   Found (3 -- remove blanks): " + name + " --> "+url)

    else:
        print("   Not found: "+jname)

    # If that didn't work, see if we have a match in the list of external links
    if name == None:
        for ex in externalLinks1942:
            if jname.lower() == ex.Title.lower():
                name=ex.Title
                url=ex.URL
                print("   Found (3): " + name + " --> " + url)
                break
            else:
                # Try adding a trailing ", the" since sometimes Joe's list omits this
                if (jname.lower() + ", the") == ex.Title.lower():
                    name=ex.Title
                    url=ex.URL
                    print("   Found (4): " + name + " --> " + url)
                    break
    if name == None:
        print("   Not found (5): " + jname)

    # Update the 1942 fanzines list with the new information
    allFanzines1942[i]=ExpandedData(Name=fanzine.Name, Editor=fanzine.Editor, Stuff=fanzine.Stuff, IsHugoEligible=isHugoEligible, NameOnFanac=name, URL=Helpers.RelPathToURL(url), Issues=None)

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

    if fz.Stuff == None:    # Skip empty stuff
        continue
    stuff="".join(fz.Stuff.split()) # Compress out whitespace
    if len(stuff) == 0:     # Skip if it's allwhitespace
        continue
    spl=stuff.split(",")
    if len(spl) == 0:       # Probably can't happen
        continue

    # OK, spl is now a list of one or more comma-separated items from Stuff
    # See if they're all interpretable as issue numbers
    listOfIssues=[]     # A list of issue tuples to be created
    someGood=False
    someBad=False
    for s in spl:
        iss=IssueNumber(*Helpers.DecodeIssueDesignation(s))
        if iss.Num == None:
            someBad=True
            continue
        else:
            someGood=True
            listOfIssues.append(iss)

    if someGood:
        allFanzines1942[i]=allFanzines1942[i]._replace(Issues=listOfIssues)

    if someBad:
        print("Not all interpretable: "+str(spl))

del someGood, someBad, s, spl, i, stuff, listOfIssues, iss
print("----Done decoding issue list in list of all 1942 fanzines")



#============================================================================================
print("----Begin generating the HTML")
f=open("1942.html", "w")
f.write("<body>\n")
f.write('<style>\n')
f.write('<!--\n')
f.write('p            { line-height: 100%; margin-top: 0; margin-bottom: 0 }\n')
f.write('-->\n')
f.write('</style>\n')
f.write('<table border="0" cellspacing="0" cellpadding="0" style="margin-top: 0; margin-bottom: 0">\n')
f.write('<tr>\n')
f.write('<td valign="top" align="left">\n')
f.write('<ul>\n')

# Create the HTML file
linecount=0
for fz in allFanzines1942:
    print("   Writing HTML for: "+str(fz))

    htm=None
    if fz.IsHugoEligible:
        name=fz.Name.title()    # Joe has eligible name all in UC.   Make them normal title case.
        if name != None and fz.URL != None:
            # We have full information for an eligible zine
            txt="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+name+"</a>"
            htm='<i><a href="'+fz.URL+'">'+name+'</a></i>&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp;'+" ("+fz.Editor+") <br>"+FanacOrgReaders.FormatStuff(fz)
        elif name != None and fz.URL == None:
            # We're missing a URL for an eligible zine
            txt="Eligible:  "+name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+name+"</i>"+'&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp; ('+fz.Editor+") <br>"+FanacOrgReaders.FormatStuff(fz)
        else:
            # We're missing all information from fanac.org for an eligible fanzine -- it isn't there
            txt=name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+'</i>&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp; ('+fz.Editor+") <br>"+FanacOrgReaders.FormatStuff(fz)
    else:
        if fz.Name != None and fz.URL != None:
            # We have full information for an ineligible zine
            txt=fz.Name+" ("+fz.Editor+") "+fz.Stuff+'     <a href="'+fz.URL+'">'+fz.Name+"</a>"
            htm='<i><a href="'+fz.URL+'">'+fz.Name+"</a></i>"+" ("+fz.Editor+") <br>"+FanacOrgReaders.FormatStuff(fz)
        elif fz.Name != None and fz.URL == None:
            # We're missing a URL for an ineligible item
            txt=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+"</a></i>"+" ("+fz.Editor+") <br>"+FanacOrgReaders.FormatStuff(fz)
        else:
            # We're missing all information from fanac.org for an ineligible fanzine -- it isn't there
            txt=fz.Name+" ("+fz.Editor+") "+fz.Stuff
            htm='<i>'+fz.Name+"</i> ("+fz.Editor+") <br>"+FanacOrgReaders.FormatStuff(fz)
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