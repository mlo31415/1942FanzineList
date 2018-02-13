from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import re

FanacName=collections.namedtuple("FanacName", "FanacDirName, JoesName, DisplayName, FanacIndexName, RetroName")

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
                FanacNames.AddFanacNameDirname(name, dirname)
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
        # We apparently have a data line. Split it into tokens. Remove leading and traling blanks, but not internal blanks.
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
def ReadFanacFanzineIndexPage(fanzineName, directoryUrl, format, fanzineIssueList):
    FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName, IssueName, Vol, Number, URL")

    # Download the index.html which lists all of the issues of the specified currently on the site
    h = requests.get(directoryUrl)

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
        row=[]      # Row: fanzinename, url, year, vol, num

        # Now for code which depends on the index,html file format
        if format[0] == 0 and format[1] == 0:   # The default case

            row=(*Helpers.GetHrefAndTextFromTag(tableRow[issueCol]), tableRow[yearCol].string, None, None)    # (We ignore the Vol and Num for now.)
            # Get the num from the name
            rows.append(row)

        elif format[0] == 1 and (format[1] == 6 or format[1] == 7): # The name in the title colum ends in V<n>, #<n>

            # We need two things: The contents of the first (linking) column and the year.
            name, href=Helpers.GetHrefAndTextFromTag(tableRow[issueCol])
            p=re.compile("(.*)V([0-9]+),?\s*#([0-9]+)\s*$")
            m=p.match(name)
            if m.groups == 3:
                row=(fanzineName, href, tableRow[yearCol].string, int(m.groups[1]), int(m.groups[2]))



#     FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName, IssueName, Vol, Number, URL")

    # Now select just the fanzines for 1942 and append them to the fanzineIssueList
    for row in rows:
        if row[2] == "1942":
            print(row[0])
            issue=FanacIssueInfo(fanzineName, row[0], row[2], row[3], row[1])
            fanzineIssueList.append(issue)

    return fanzineIssueList