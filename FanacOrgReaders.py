from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import re

global g_FanacFanzineDirectoryFormats
g_FanacFanzineDirectoryFormats=None

# # This is a dictionary of all fanzines on fanac.org. The key is the fanzines name, the value is the directory name
# global fanacDirectories
# fanacDirectories={}

FanacName=collections.namedtuple("FanacName", "FanacDirName, JoesName, DisplayName, FanacIndexName, RetroName")

class FanacDirectories:

    def __init__(self):
        self.directories={}
        self.index=0

    # ======================================================================
    # We have a name and a dirname from the fanac.org Classic and Modern pages.
    # The dirname *might* be a URL in which case it needs to be handled as a foreign directory reference
    def AddDirectory(self, name, dirname):
        isDup=False

        name=name.lower()

        if name in self.directories:
            print("   duplicate: name="+name+"  dirname="+dirname)
            return

        if dirname[:3]=="http":
            print("    ignored, because is HTML: "+dirname)
            return

        # Add name and directory reference
        print("   added to fanacDirectories: name='"+name+"'  dirname='"+dirname+"'")
        self.directories[name]=dirname
        return

    def Dict(self):
        return self.directories

    def Contains(self, name):
        return name in self.directories

    def GetTuple(self, name):
        if not name in self.directories.keys():
            return None
        return (name, self.directories[name])

    def len(self):
        return len(self.directories)

    # def __iter__(self):
    #     return self
    #
    # def __next__(self):
    #     if self.index == len(self.directories):
    #         raise StopIteration
    #     self.index = self.index + 1
    #     return self.directories.items()[self.index]

# End of class FanacDirectories:
#==========================================================

g_FanacDirectories=FanacDirectories()

#====================================================================================
# Read fanac.org/fanzines/Classic_Fanzines.html amd /Modern_Fanzines.html
# Read the table to get a list of all the fanzines on Fanac.org
# Return a list of tuples (name on page, name of directory)
#       The name on page is the display named used in the Classic and Modern tables
#       The name of directory is the name of the directory pointed to

def ReadClassicModernPages():
    fanzinesList=[]
    print("----Begin reading Classic and Modern tables")

    ReadModernOrClassicTable("http://www.fanac.org/fanzines/Classic_Fanzines.html")
    ReadModernOrClassicTable("http://www.fanac.org/fanzines/Modern_Fanzines.html")

    print("----Done reading Classic and Modern tables")
    return


#======================================================================
def ReadModernOrClassicTable(url):
    h=requests.get(url)
    s=BeautifulSoup(h.content, "html.parser")
    # We look for the first table that does ot contain a "navbar"
    tables=s.body.find_all("table")
    for table in tables:
        if "sortable" in str(table.attrs) and not "navbar" in str(table.attrs):
            # OK, we've found the main table.  Now read it
            trs=table.find_all("tr")
            for i in range(1, len(trs)-1):
                # Now the data rows
                name=trs[i].find_all("td")[1].contents[0].contents[0].contents[0]
                dirname=trs[i].find_all("td")[1].contents[0].attrs["href"][:-1]
                g_FanacDirectories.AddDirectory(name, dirname)
    return


# ============================================================================================
def ReadFanacOrgFormatsTxt():
    # print("----Begin reading Fanac fanzine directory formats.txt")
    # FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName, IssueName, Vol, Number, URL")
    FanacDirectoryFormat=collections.namedtuple("FanacDirectoryFormat", "Num1, Num2, DirName")
    # Next we read the table of fanac.org file formats.
    # Fanac.org's fanzines are *mostly* in one format, but there are at least a dozen different ways of presenting them.
    # The table will allow us to pick the right method for reading the index.html file and locating the right issue URL
    try:
        f=open("Fanac fanzine directory formats.txt", "r")
    except:
        print("Can't open 'Fanac fanzine directory formats.txt'")
        exit(0)
    # Read the file.  Lines beginning with a # are comments and are ignored
    # Date lines consist of a commz-separated list:
    #       The first two elements are code numbers
    #       The remaining elements are directories in fanac.org/fanzines
    #       We create a dictionary of fanzine directory names in lower case.
    #       The value of each directory entry is a tuple consisting of Name (full case) folowed by the two numbers.
    fanacFanzineDirectoryFormats={}
    for line in f:
        line=line.strip()  # Make sure there are no leading or traling blanks
        if len(line)==0 or line[0]=="#":  # Ignore some lines
            continue
        # We apparently have a data line. Split it into tokens. Remove leading and trailing blanks, but not internal blanks.
        spl=line.split(",")
        if len(spl)<3:  # There has to be at least three tokens (the two numbers and at least one directory name)
            print("***Something's wrong with "+line)
            continue
        nums=spl[:2]
        spl=spl[2:]
        for dir in spl:
            fanacFanzineDirectoryFormats[dir.lower().strip()]=FanacDirectoryFormat(int(nums[0]), int(nums[1]), dir)
    print("----Done reading Fanac fanzine directory formats.txt")

    return fanacFanzineDirectoryFormats


# ============================================================================================
# Function to extract information from a fanac.org fanzine index.html page
def ReadAndAppendFanacFanzineIndexPage(fanzineName, directoryUrl, format, fanzineIssueList):
    skippers=["Emu Tracks Over America", "Flight of the Kangaroo, The", "Enchanted Duplicator, The", "Tails of Fandom", "BNF of IZ", "NEOSFS Newsletter, Issue 3, The"]
    if fanzineName in skippers:
        print("   Skipping: "+fanzineName)
        return fanzineIssueList

    FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName, IssueName, Vol, Number, URL")

    # We're only prepared to read a few formats.  Skip over the others right now.
    OKFormats=((0,0), (1,6), (1,7))
    codes=(format[0], format[1])
    if not codes in OKFormats:
        print("   Can't handle format:"+str(format) +" from "+directoryUrl)
        return None

    # Download the index.html which lists all of the issues of the specified fanzine currently on the site
    try:
        h = requests.get(directoryUrl)
    except:
        try:
            h=requests.get(directoryUrl)
        except:
            print("***Request failed for: "+directoryUrl)
            return None

    s = BeautifulSoup(h.content, "html.parser")
    b = s.body.contents
    # Because the structures of the pages are so random, we need to search the body for the table.
    # *So far* all of the tables have been headed by <table border="1" cellpadding="5">, so we look for that.

    tab=Helpers.LookForTable(b)
    if tab == None:
        print("*** No Table found!")
        return None

    # OK, we probably have the issue table.  Now decode it.
    # The first row is the column headers
    # Subsequent rows are fanzine issue rows

    # Some of the items showing up in val.contents will be strings containing newlines -- start by compressing them out.
    tab.contents=Helpers.RemoveNewlineRows(tab.contents)

    # Ok. We have the table.  Make a list of the column headers. We need to compress the newlines out of this as well
    tableHeader = Helpers.RemoveNewlineRows(tab.contents[0])
    columnHeaders = []
    for col in tableHeader:
        columnHeaders.append(col.string)

    # We want to append just the rows for 1942
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
        return None
    if issueCol == None:
        print("    No issueCol found")
        return None

    # What's left is one or more rows, each corresponding to an issue of that fanzine.
    # We build up a list of lists.  Each list in the list of lists is a row
    # We have to treat the Title column specially, since it contains the critical href we need.
    rows=[]
    for i in range(1, len(tab)):
        tableRow=Helpers.RemoveNewlineRows(tab.contents[i])
        FanzineInfo=collections.namedtuple("FanzineInfo", "Name, URL, Year, Vol, Num")

        # Now for code which depends on the index,html file format
        if format[0] == 0 and format[1] == 0:   # The default case

            temp=Helpers.GetHrefAndTextFromTag(tableRow[issueCol])
            row=FanzineInfo(Name=temp[0], URL=temp[1], Year=tableRow[yearCol].string, Vol=None, Num=None)    # (We ignore the Vol and Num for now.)
            # Get the num from the name
            rows.append(row)

        elif format[0] == 1 and (format[1] == 6 or format[1] == 7): # The name in the title column ends in V<n>, #<n>

            # We need two things: The contents of the first (linking) column and the year.
            name, href=Helpers.GetHrefAndTextFromTag(tableRow[issueCol])
            p=re.compile("(.*)V([0-9]+),?\s*#([0-9]+)\s*$")
            m=p.match(name)
            if m != None and len(m.groups()) == 3:
                row=FanzineInfo(Name=fanzineName, URL=href, Year=tableRow[yearCol].string, Vol=int(m.groups()[1]), Num=int(m.groups()[2]))
                rows.append(row)


#     FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName, IssueName, Vol, Number, URL")

    # Now select just the fanzines for 1942 and append them to the fanzineIssueList
    for row in rows:
        if row.Year == "1942":
            print(str(row))
            issue=FanacIssueInfo(FanzineName=fanzineName, URL=row.URL, Number=row.Num, Vol=row.Vol, IssueName=None)
            print("1942: ReadAndAppendFanacFanzineIndexPage: appending "+str(issue))
            fanzineIssueList.append(issue)

    return fanzineIssueList


# ============================================================================================
def ReadFanacFanzineIssues(fanzinesList):
    # Read index.html files on fanac.org
    # We have a dictionary containing the names and URLs of the 1942 fanzines.
    # The next step is to figure out what 1942 issues of each we have on the website
    # We do this by reading the fanzines/<name>/index.html file and then decoding the table in it.
    # What we get out of this is a list of fanzines with name, URL, and issue info.
    # Loop over the list of all 1942 fanzines, building up a list of those on fanac.org
    print("----Begin reading index.html files on fanac.org")

    global g_FanacFanzineDirectoryFormats
    if g_FanacFanzineDirectoryFormats == None:
        g_FanacFanzineDirectoryFormats=ReadFanacOrgFormatsTxt()

    global g_fanacIssueInfo
    g_fanacIssueInfo=[]
    for title, dirname in fanzinesList.Dict().items():

        # Get the index file format for this directory
        try:
            dn=dirname.lower()
            if '/' in dirname:
                print("   skipped because of '/' in name:"+dirname)
                continue
            if not dn in g_FanacFanzineDirectoryFormats:
                print("   Not in g_FanacFanzineDirectoryFormats:"+dirname)
            fmt=g_FanacFanzineDirectoryFormats[dn]
            print("   Format: "+title+" --> "+FanacNames.StandardizeName(title.lower())+" --> "+str(fmt))
        except:
            print("   Format: "+title+" --> "+FanacNames.StandardizeName(title.lower())+" -->  (0, 0)")
            # This is actually a good thing, because it means that the fanzines has the default index.html type
            print("   fanacFanzineDirectoryFormats["+title.lower()+"] not found")

            if '/' in dirname:
                print("   skipped because of '/' in name:"+dirname)
                continue

            # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
            # We need to turn relPath into a URL
            url=Helpers.RelPathToURL(dirname)
            print(title, " ", url)
            if url == None:
                continue
            if url.startswith("http://www.fanac.org") and not url.startswith("http://www.fanac.org//fan_funds") and not url.startswith("http://www.fanac.org/fanzines/Miscellaneous"):
                ret=ReadAndAppendFanacFanzineIndexPage(title, url, (0, 0, None), g_fanacIssueInfo)
                if ret!=None:
                    g_fanacIssueInfo=ret
            continue

        if format == (8, 0):
            print("   Skipped because no index.html file: "+ dirname)
            continue

        # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
        # We need to turn relPath into a URL
        url=Helpers.RelPathToURL(dirname)
        print(title, " ", url)
        if url.startswith("http://www.fanac.org") and not url.startswith("http://www.fanac.org//fan_funds"):
            ret=ReadAndAppendFanacFanzineIndexPage(title, url, fmt, g_fanacIssueInfo)
            if ret!=None:
                g_fanacIssueInfo=ret

    # Now we have a list of all the issues of fanzines onfanac.org which have at least one 1942 issue.(Not all of the issues are 1942.)
    print("----Done reading index.html files on fanac.org")
    return


#================================================================================================
# Inline function to format Stuff, which is a list of IssueSpecs
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
        if issue.Vol == None and issue.Num == None: # We haved neither Vol nor Num
            v="(oops) "+ fz.Stuff

        elif issue.Vol == None:     # We have Num, but not Vol
            # Look up the fanzine to see if it is on fanac.org. The look up the Vol/Issue to see if it is there.
            if fz.NameOnFanac != None:
                name=fz.NameOnFanac
            else:
                name=fz.Name
            val=g_FanacDirectories.GetTuple(name)
            if val == None:
                print("   FormatStuff can't find the directory for "+str(fz))
                continue
            dirname=val[1]
            if dirname == None:
                print("   FormatStuff can't find the directory (2) for "+str(fz))
                continue

            # OK, let's create the formatted output
            url=None
            text=None
            if dirname.startswith("dirname"):   # Can this still happen?
                url="Oops"
                v="Oops"
            else:
                for fii in g_fanacIssueInfo:
                    if Helpers.CompareIssueSpec(fii.FanzineName, fii.Vol, fii.Number, dirname, issue.Vol, issue.Num):
                        url=fii.URL
                        text=str(issue.Num)
                        break
                if url != None:
                    v=Helpers.FormatLink(str(issue.Num), url)
                else:
                    v="#"+str(issue.Num)
        else:
            v="V"+str(issue.Vol)+"#"+str(issue.Num)

        if len(out) > 0:
            out=out+", "
        out=out+v
    return out

