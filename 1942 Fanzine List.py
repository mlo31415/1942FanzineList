import collections
import Helpers
import FanacNames
import FanacOrgReaders
import RetroHugoReaders
import FanzineData

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

for i in range(0, len(allFanzines1942)):
    fanzine=allFanzines1942[i]

    # First we take the fanzine name from Joe's 1942 Fanzine List.txt and match it to a 1942 fanzine on fanac.org
    jTitle=fanzine.title

    isHugoEligible=False        # Joe has tagged Hugo-eligible fanzines by making their name to be all-caps
    if jTitle == jTitle.upper():
        isHugoEligible=True

    # listOf1942s is a dictionary of 1942 fanzines that we have on fanac.org. The key is the fanzine name in lower case
    # the value is a tuple of the fanzine name and the URL on fanac.org
    # We want to look up the entries from Joe's list and see if they are on it.
    name=None
    url=None
    tpl=FanacOrgReaders.FanacDirectories().GetTuple(jTitle)
    if tpl != None:
        name, url=tpl
        print("   Found (1): "+name +" --> " + url)
    else:
        print("   Not found in g_FanacDirectories: "+jTitle)

    allFanzines1942[i].SetIsHugoEligible(isHugoEligible)
    if name != None:
        # Update the 1942 fanzines list with the new information
        allFanzines1942[i].SetFanacDirName(url)
        allFanzines1942[i].SetFanacFanzineName(name)
        allFanzines1942[i].SetURL(Helpers.RelPathToURL(url))


del fanzine, jTitle, name, url, i, isHugoEligible, tpl
print("----Done combining information into one table.")


#============================================================================================
print("----Begin decoding issue list in list of all 1942 fanzines")
# Define a named tuple to hold the an issue number
IssueNumber=collections.namedtuple("IssueNumber", "Vol Num")

# OK, now the problem is to decode the crap to form a list of issue numbers...or something...
for index in range(0, len(allFanzines1942)):
    fz=allFanzines1942[index]
    print("   Decoding issue list: "+ str(fz))

    stuff=fz.issuesText
    if stuff == None:    # Skip empty stuff
        continue
    if len("".join(stuff.split())) == 0: # Skip if it's all whitespace by splitting on whitespace, joining the remnants and counting the remaining characters
        continue

    # Turn all multiple spaces into a single space
    stuff=stuff.replace("  ", " ").replace("  ", " ").replace("  ", " ").strip()   # Hopefully there's never more than 8 spaces in succession...

    issueSpecList=FanacNames.IssueSpecList()   # This will be the list of IssueSpecs resulting from interpreting stuff

    # Cases:
    #   1,2,3,4
    #   V1#2, V3#4
    #   V1#2,3 or V1:2,3
    #   1942:5
    #   210-223
    #   Sometimes a semicolon is used as a separator....
    #   The different representations can be intermixed.  This causes a problem because the comma winds up having different meanings in different cases.
    #   Stuff in parentheses will always be treated as comments
    #   Trailing '?' will be ignored
    #   And sometimes there is odd stuff tossed in which can't be interpreted.

    # The strategy is to take the string character by character and whittle stuff down as we interpret it.
    # The intention is that we come back to the start of the look each time we have disposed of a chunk of characters, so that the next character should start a new issue designation
    # There are four basic patterns to be seen in Joe's data:
    #   A comma-separated list of issue whole numners
    #   A list of Volumes and numbers (many delimiter patterns!)
    #   A range of whole numbers
    #   A list of year:issue pairs
    #  In all cases we need to be prepared to deal with (and preserve) random text.
    iss=[]
    while len(stuff) > 0:

        issueSpecs=None
        stuff=stuff.strip()  # Leading and trailing whitespace is uninteresting

        # If the first character is a "V", we have a volume followed by one or more issues all in that volume
        # Sometimes there will be another Vn indicating a new volume
        # A V which begins a volume-num sequence *always* has the pattern <delimiter>V<digit>, where start-of-line counts as a delimiter.
        # Because we've trimmed off leading whitespace, we can detected the first:
        if (len(stuff) > 1 and stuff[0].lower() == "v" and stuff[1].isdigit()):
            while len(stuff)>0:
                # Look for the termination of the first Volume-num list. It ends at another Volume-Num list or at eol
                locNextVlist=None
                for i in range(1, len(stuff)-3):
                    if (stuff[i-1] == " " or stuff[i-1] == ";") and stuff[i].lower() == "v" and stuff[i+1].isdigit():
                        locNextVlist=i
                        break
                if locNextVlist == None:
                    locNextVlist=len(stuff)
                vlist=stuff[:locNextVlist-1]
                stuff=stuff[locNextVlist:]

                iss=FanacNames.InterpretVolNumSpecText(vlist)

                if iss != None:
                    issueSpecList.Append(iss)
            break


        # It's not a Vn#n sort of thing, but maybe it's a list of whole numbers
        # It must start with a digit
        elif stuff[0].isdigit():
            loc=stuff.find(",")
            if loc == -1:
                loc=stuff.find(";")
                if loc == -1:   # Must be eol
                    loc=len(stuff)
            rslt=FanacNames.InterpretWholenumSpecText(stuff[:loc])
            if rslt != None:
                issueSpecList.Append(rslt)
                stuff=stuff[loc+1:]
            else:
                print("***FanacNames.InterpretWholenumSpecText returned None from"+stuff[:loc-1])

        # OK, it's probably junk. Absorb everything until the next V-spec or digit
        else:
            parenLevel=0
            end=None
            for i in range(0, len(stuff)):
                if stuff[i] == "(":
                    parenLevel=parenLevel+1
                if stuff[i] == ")":
                    parenLevel=parenLevel+1
                if parenLevel > 0:
                    continue    # If we're inside a parenthesis, anything goes until we're out of it again.
                if stuff[i].lower() == 'v' or stuff[i].isdigit():
                    end=i
                    break
            if end == None:
                end=len(stuff)
            garbage=stuff[:end]
            stuff=stuff[end:]
            issueSpecList.Append1(FanacNames.IssueSpec().SetGarbage(garbage))

    print("   "+issueSpecList.Print())

    allFanzines1942[index].SetIssues(issueSpecList)    # Just update the one field


del i, stuff, iss, loc, issueSpecs, index, fz, end, garbage, parenLevel, vlist, locNextVlist
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
for fz in allFanzines1942:  # fz is a FanzineData class object
    print("   Writing HTML for: "+str(fz))

    htm=None
    if fz.isHugoEligible:
        name=fz.title.title()    # Joe has eligible name all in UC.   Make them normal title case.
        if name != None and fz.url != None:
            # We have full information for an eligible zine
            txt="Eligible:  "+name+" ("+fz.editors+") "+fz.issuesText+'     <a href="'+fz.url+'">'+name+"</a>"
            htm='<i><a href="'+fz.url+'">'+name+'</a></i>&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp;'+" ("+fz.editors+") <br>"+FanacOrgReaders.FormatStuff(fz)
        elif name != None and fz.url == None:
            # We're missing a URL for an eligible zine
            txt="Eligible:  "+name+" ("+fz.editors+") "+fz.issuesText
            htm='<i>'+name+"</i>"+'&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp; ('+fz.editors+") <br>"+FanacOrgReaders.FormatStuff(fz)
        else:
            # We're missing all information from fanac.org for an eligible fanzine -- it isn't there
            txt=name+" ("+fz.editors+") "+fz.issuesText
            htm='<i>'+name+'</i>&nbsp;&nbsp;<font color="#FF0000">(Eligible)</font>&nbsp;&nbsp; ('+fz.editors+") <br>"+FanacOrgReaders.FormatStuff(fz)
    else:
        name=fz.title.title()
        if fz.title != None and fz.url != None:
            # We have full information for an ineligible zine
            txt=name+" ("+fz.editors+") "+fz.issuesText+'     <a href="'+fz.url+'">'+fz.title+"</a>"
            htm='<i><a href="'+fz.url+'">'+fz.title+"</a></i>"+" ("+fz.editors+") <br>"+FanacOrgReaders.FormatStuff(fz)
        elif fz.title != None and fz.url == None:
            # We're missing a URL for an ineligible item
            txt=name+" ("+fz.editors+") "+fz.issuesText
            htm='<i>'+name+"</a></i>"+" ("+fz.editors+") <br>"+FanacOrgReaders.FormatStuff(fz)
        else:
            # We're missing all information from fanac.org for an ineligible fanzine -- it isn't there
            txt=name+" ("+fz.editors+") "+fz.issuesText
            htm='<i>'+name+"</i> ("+fz.editors+") <br>"+FanacOrgReaders.FormatStuff(fz)
    linecount=linecount+1
    if linecount == round(len(allFanzines1942)/2):
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
    if fz.fanacDirName == None or fz.url == None:
        f2.write(fz.title+"\n")
f2.flush()
f2.close()
del f2, htm, txt, fz

print("----Done generating the HTML")


i=0