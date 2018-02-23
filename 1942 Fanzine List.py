from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import FanacOrgReaders
import RetroHugoReaders

#--------------------------------------
# Overall Strategy
# (1) Read fanac.org's fanzine index pages to get a list of all the fanzines represented including name and directory name.  (We don't at this time read the actual data.)
#       FanacOrgReaders.ReadClassicModernPages()
# (2) Read Joe's list of all 1942 fanzines.  This includes information on what fanzines are eligible for the 1942 Retro Hugo
#   We add those names to the fanzine dictionary, also.
#   We create a list of all 1942 fanzines including issue info.
#       allFanzines1942=RetroHugoReaders.Read1942FanzineList()
# (3) Read a list of links to individual fanzines not on fanac.org
#       Done in code when ExternalLinks class is instantiated
# (4) Go through the fanzines directories on fanac.org, and get a list of issues present, including the links to the scans
#     This also loads the table of fanac.org directory index.html types
#       FanacOrgReaders.ReadFanacFanzineIssues(FanacOrgReaders.g_FanacDirectories)
# (5) Combine the information into a single grand table of fanzines which includes links to the issues
# (6) Go through Joe's list and try to interpret the issue designations and match them with other sources
# (7) Generate the output HTML
#--------------------------------------

# Create the list of FanacName tuples which will be used by FanacName functions
# Note: This is just to get the names and directories, nothing else.
FanacNames.AddFanacDirectories(FanacOrgReaders.FanacDirectories().Dict())      # Add them to g_fanacNameTuples, which is managed and accessed by FanacNames

# Read Joe's PDF and create a list of tuples, each representing one of the complete set of fanzines of 1942
# The three items of the tuple are the fanzine name, the fanzine editors, andf the fanzine issue data.
# Some of this is pretty rough, being taken from somewhat inconsistant text in the PDF.
# This will also add any new names found to the FanacNames tuples
allFanzines1942=RetroHugoReaders.Read1942FanzineList()

# Read the fanac.org fanzine direcgtory and produce a lost of all issues present
FanacOrgReaders.ReadFanacFanzineIssues()

#============================================================================================
print("----Begin combining information into one table.")
# Now we go through the list we just parsed and generate the output document.
#   1. We link the fanzine name to the fanzine page on fanac.org
#   2. We link each issue number to the individual issue
#   3. We highlight those fanzines which are eligible for a 1942 Hugo

# Define a named tuple to hold the expanded data I get by combining all the sources
ExpandedData=collections.namedtuple("ExpandedData", "Name Editor Stuff IsHugoEligible FanacDirName FanacFanzineName URL Issues")

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
    tpl=FanacOrgReaders.FanacDirectories().GetTuple(jname)
    if tpl != None:
        name, url=tpl
        print("   Found (1): "+name +" --> " + url)
    else:
        print("   Not found in g_FanacDirectories: "+jname)

    if name != None:
        # Update the 1942 fanzines list with the new information
        allFanzines1942[i]=ExpandedData(Name=fanzine.Name, Editor=fanzine.Editor, Stuff=fanzine.Stuff, IsHugoEligible=isHugoEligible, FanacDirName=url, FanacFanzineName=name, URL=Helpers.RelPathToURL(url), Issues=None)
    else:
        allFanzines1942[i]=ExpandedData(Name=fanzine.Name, Editor=fanzine.Editor, Stuff=fanzine.Stuff, IsHugoEligible=isHugoEligible, FanacDirName=None, FanacFanzineName=None, URL=None, Issues=None)

del fanzine, jname, name, url, i, isHugoEligible, tpl
print("----Done combining information into one table.")


#============================================================================================
print("----Begin decoding issue list in list of all 1942 fanzines")
# Define a named tuple to hold the an issue number
IssueNumber=collections.namedtuple("IssueNumber", "Vol Num")

# OK, now the problem is to decode the crap at the end to form a list of issue numbers...or something...
for i in range(0, len(allFanzines1942)):
    fz=allFanzines1942[i]
    print("   Decoding issue list: "+ str(fz))

    stuff=fz.Stuff
    if stuff == None:    # Skip empty stuff
        continue
    if len("".join(stuff.split())) == 0: # Skip if it's all whitespace by splitting on whitespace, joining the remnants and counting the remaining characters
        continue

    # Turn all multiple spaces into a single space
    stuff=stuff.replace("  ", " ").replace("  ", " ").replace("  ", " ").strip()   # Hopefully there's never more than 8 spaces in succession...

    issueSpecList=FanacNames.IssueSpecList()   # This will be the resulting list of IssueSpecs

    # Cases:
    #   1,2,3,4
    #   V1#2, V3#4
    #   V1#2,3 or V1:2,3
    #   Sometimes a semicolon is used as a separator....
    #   The different representations can be intermixed.  This causes a problem because the comma winds up having different meanings in different cases.
    #   Stuff in parentheses will always be treated as comments
    #   Trailing '?' will be ignored
    #   And sometimes there is odd stuff tossed in which can't be interpreted.

    # The strategy is to take the string chacater by character and whittle stuff down as we interpret it.
    # The intentionn is that we come back to the start of the look each time we have disposed of a chunk of characters, so that the next character should start a new issue designation
    while len(stuff) > 0:
        # If the first character is a "V", we have either a volume-issue pair or a volume followed by a list of issues all in that volume
        # We can distinguish a list of issues because Joe never (well, hardly ever!) puts a space in the related list
        issueSpecs=None
        stuff=stuff.strip()  # Leading and trailing whitespace is uninteresting
        if (stuff[0].lower() == "v"):
            # Look for a subsequent ", " or eol or ";"
            loc=stuff.find(", ")
            if loc == -1:
                loc=stuff.find("; ")
            if loc == -1 or loc+2 > len(stuff):
                # This spec appears to extend to the end of the string
                specStr=stuff
                stuff=""
            else:
                specStr=stuff[:loc].strip()
                stuff=stuff[loc+2:].strip()

            iss=FanacNames.InterpretIssueSpecText(specStr)

            if iss != None:
                issueSpecList.Append(iss)

        # It's not a Vn#n sort of thing, but maybe it's a list of whole numbers
        # It must start with a digit
        elif stuff[0].isdigit():
            loc=stuff.find(",")
            if loc == -1:
                loc=stuff.find(";")
            try:
                if loc != -1:
                    specStr=stuff[:loc]
                    stuff=stuff[loc+1:].strip()
                    issueSpecList.Append([FanacNames.IssueSpec().Set1(int(specStr))])
                else:
                    issueSpecList.Append([FanacNames.IssueSpec().Set1(int(stuff))])
                    stuff=""
            except:
                # If we encounter an open parenthesis, it and its contents are treated as uninterpretable text
                stuff=stuff.strip()
                if stuff[0] == "(":
                    # Find closing ")"
                    loc=stuff.find(")")
                    if loc > 0:
                        specStr=stuff[:loc]
                        stuff=stuff[loc+1:]
                        issueSpecList.Append1(FanacNames.IssueSpec().SetGarbage(specStr))
                        continue
                stuff=""    # TODO: Should try to recover so any later specs can be interpreted
                continue

    print("   "+issueSpecList.Print())

    allFanzines1942[i]=allFanzines1942[i]._replace(Issues=issueSpecList)


del i, stuff, iss, loc, specStr, issueSpecs
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
    print(htm)
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
    if fz.FanacDirName == None or fz.URL == None:
        f2.write(fz.Name+"\n")
f2.flush()
f2.close()
del f2, htm, txt, fz

print("----Done generating the HTML")


i=0