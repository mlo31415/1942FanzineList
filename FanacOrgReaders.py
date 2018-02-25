from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import re
import FanacDirectoryFormats

# ===============================================================================
# This is a class to manage the list of fanzine directories in fanac.org

global g_FanacDirectories   # This is global to share a single instance of the data among all instances of the class, *not* to allow access except through class members
g_FanacDirectories={}

class FanacDirectories:

    def __init__(self):
        global g_FanacDirectories
        if len(g_FanacDirectories) == 0:
            self.ReadClassicModernPages()

    def Dict(self):
        return g_FanacDirectories

    # -------------------------------------------------------------------------
    # We have a name and a dirname from the fanac.org Classic and Modern pages.
    # The dirname *might* be a URL in which case it needs to be handled as a foreign directory reference
    def AddDirectory(self, name, dirname):
        isDup=False

        if name in g_FanacDirectories:
            print("   duplicate: name="+name+"  dirname="+dirname)
            return

        if dirname[:3]=="http":
            print("    ignored, because is HTML: "+dirname)
            return

        # Add name and directory reference\
        cname=Helpers.CompressName(name)
        print("   added to fanacDirectories: key='"+cname+"'  name='"+name+"'  dirname='"+dirname+"'")
        g_FanacDirectories[cname]=(name, dirname)
        return

    def Contains(self, name):
        return Helpers.CompressName(name) in g_FanacDirectories

    def GetTuple(self, name):
        if self.Contains(name):
            return g_FanacDirectories[Helpers.CompressName(name)]
        if self.Contains(name+"the"):
            return g_FanacDirectories[Helpers.CompressName(name+"the")]
        if self.Contains(name+"an"):
            return g_FanacDirectories[Helpers.CompressName(name+"an")]
        if self.Contains(name+"a"):
            return g_FanacDirectories[Helpers.CompressName(name+"a")]
        return None

    def len(self):
        return len(g_FanacDirectories)

    # ====================================================================================
    # Read fanac.org/fanzines/Classic_Fanzines.html amd /Modern_Fanzines.html
    # Read the table to get a list of all the fanzines on Fanac.org
    # Return a list of tuples (name on page, name of directory)
    #       The name on page is the display named used in the Classic and Modern tables
    #       The name of directory is the name of the directory pointed to

    def ReadClassicModernPages(self):
        fanzinesList=[]
        print("----Begin reading Classic and Modern tables")

        self.ReadModernOrClassicTable("http://www.fanac.org/fanzines/Classic_Fanzines.html")
        self.ReadModernOrClassicTable("http://www.fanac.org/fanzines/Modern_Fanzines.html")

        print("----Done reading Classic and Modern tables")
        return

    # ======================================================================
    def ReadModernOrClassicTable(self, url):
        h=requests.get(url)
        s=BeautifulSoup(h.content, "html.parser")
        # We look for the first table that does ot contain a "navbar"
        tables=s.body.find_all("table")
        for table in tables:
            if "sortable" in str(table.attrs) and not "navbar" in str(table.attrs):
                # OK, we've found the main table.  Now read it
                trs=table.find_all("tr")
                for i in range(1, len(trs)):
                    # Now the data rows
                    name=trs[i].find_all("td")[1].contents[0].contents[0].contents[0]
                    dirname=trs[i].find_all("td")[1].contents[0].attrs["href"][:-1]
                    self.AddDirectory(name, dirname)
        return

# End of class FanacDirectories


# ============================================================================================
# Function to extract information from a fanac.org fanzine index.html page
def ReadAndAppendFanacFanzineIndexPage(fanzineName, directoryUrl, format, fanzineIssueList):
    skippers=["Emu Tracks Over America", "Flight of the Kangaroo, The", "Enchanted Duplicator, The", "Tails of Fandom", "BNF of IZ", "NEOSFS Newsletter, Issue 3, The"]
    if fanzineName in skippers:
        print("   Skipping: "+fanzineName)
        return fanzineIssueList

    FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName, IssueName, Vol, Number, URL")

    # We're only prepared to read a few formats.  Skip over the others right now.
    OKFormats=((0,0), (1,6))
    codes=(format[0], format[1])
    if not codes in OKFormats:
        print("      Can't handle format:"+str(format) +" from "+directoryUrl)
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
    # The first row of the table contains the table header
    tableRow = Helpers.RemoveNewlineRows(tab.contents[0])
    chl=[]
    for col in tableRow:
        chl.append(col.string.replace(" ",""))      # Can't have internal spaces
    columnHeaders=" ".join(chl)
    print("   columnHeaders="+columnHeaders)
    del chl

    # Remove some sloppy column header stuff and characters that are OK, but which can't be in Namedtuple field names
    columnHeaders=columnHeaders.replace("Vol/#", "VolNum").replace("Vol./#", "VolNum")
    columnHeaders=columnHeaders.replace("#", "Num")
    columnHeaders=columnHeaders.replace("/", "").replace("Mo.", "Month").replace("Pp.", "Pages")
    # And can you believe duplicate column headers?
    if len(columnHeaders.split(" Number "))>2:
        columnHeaders=columnHeaders.replace(" Number ", " Whole ", 1) # If Number appears twice, replace the first with Whole

    FanzineTable=collections.namedtuple("FanzineTable", columnHeaders)

    # What's left is one or more rows, each corresponding to an issue of that fanzine.
    # We build up a list of lists.  Each list in the list of lists is a row
    # We have to treat the Title column specially, since it contains the critical href we need.
    fanzineTable=[]
    for i in range(1, len(tab)):
        tableRow=Helpers.RemoveNewlineRows(tab.contents[i])
        r=[]
        for j in range(0, len(tableRow)):
            try:        # If the tag contains an href, we save the tag/.  Otherwise, just the text
                tableRow[j].contents[0].attrs.get("href", None)
                r.append(tableRow[j])
            except:
                r.append(tableRow[j].text)
        print("   row=" + str(r))
        fanzineTable.append(FanzineTable(*r))

    # Now we have the entire fanzine table stored in fanzineTable
    # We need to extract the name, url, year, and vol/issue info for each fanzine
    FanzineInfo=collections.namedtuple("FanzineInfo", "Name, URL, Year, Vol, Num")  # Define a named tuple to hold the info

    # We have to treat the Title column specially, since it contains the critical href we need.
    rows=[]
    for row in fanzineTable:

        # Figure out how to get a year
        # There may be a year column or there may be a date column
        year=None
        try:
            if "Year" in row._fields:
                year=int(row.Year)
            elif "Date" in row._fields:
                date=Helpers.InterpretDateString(row.Date)
                if date != None:
                    year=date.Year
        except:
            year=None   # Gotta have *some* code in the except clause

        if year == None:
            print("   ***Can't find year")
            continue

        # Now find the column containing the issue designation. It could be "Issue" or "Title"
        issueCol=None
        for i in range(0, len(row._fields)):
            if row._fields[i] == "Issue":
                issueCol= i
                break
        if issueCol == None:
            for i in range(0, len(row._fields)):
                if row._fields[i]=="Title":
                    issueCol=i
                    break
        if issueCol == None:
            print("  ***No IssueCol")
            continue

        # Now for code which depends on the index,html file format
        if format[0] == 0 and format[1] == 0:   # The default case

            # Get the num from the name
            name, href=Helpers.GetHrefAndTextFromTag(row[issueCol])
            if href == None:
                print("    skipping: "+name)
                continue

            p=re.compile("^.*\D([0-9]+)\s*$")
            m=p.match(name)
            num=None
            if m != None and len(m.groups()) == 1:
                num=int(m.groups()[0])

            fi=FanzineInfo(Name=name, URL=href, Year=year, Vol=None, Num=num)    # (We ignore the Vol and Num for now.)
            print("   (0,0): "+str(fi))
            rows.append(fi)

        elif format[0] == 1 and format[1] == 6: # The name in the title column ends in V<n>, #<n>

            # We need two things: The contents of the first (linking) column and the year.
            name, href=Helpers.GetHrefAndTextFromTag(row[issueCol])
            if href==None:
                print("    skipping: "+name)
                continue

            p=re.compile("(.*)V([0-9]+),?\s*#([0-9]+)\s*$")
            m=p.match(name)
            if m != None and len(m.groups()) == 3:
                fi=FanzineInfo(Name=fanzineName, URL=href, Year=year, Vol=int(m.groups()[1]), Num=int(m.groups()[2]))
                print("   (1,6): "+str(fi))
                rows.append(fi)

    # Now select just the fanzines for 1942 and append them to the fanzineIssueList
    for row in rows:
        if row.Year == 1942:
            print("      "+str(row))
            issue=FanacIssueInfo(FanzineName=fanzineName, URL=row.URL, Number=row.Num, Vol=row.Vol, IssueName=None)
            print("      1942: ReadAndAppendFanacFanzineIndexPage: appending "+str(issue))
            fanzineIssueList.append(issue)

    return fanzineIssueList


# ============================================================================================
def ReadFanacFanzineIssues():
    # Read index.html files on fanac.org
    # We have a dictionary containing the names and URLs of the 1942 fanzines.
    # The next step is to figure out what 1942 issues of each we have on the website
    # We do this by reading the fanzines/<name>/index.html file and then decoding the table in it.
    # What we get out of this is a list of fanzines with name, URL, and issue info.
    # Loop over the list of all 1942 fanzines, building up a list of those on fanac.org
    print("----Begin reading index.html files on fanac.org")

    global g_fanacIssueInfo
    g_fanacIssueInfo=[]
    for key, (title, dirname) in FanacDirectories().Dict().items():
        print("'"+key+"', "+title+"', "+dirname+"'")
        if '/' in dirname:
            print("   skipped because of '/' in name:"+dirname)
            continue

        # Get the index file format for this directory
        format=FanacDirectoryFormats.FanacDirectoryFormats().GetFormat(dirname.lower())
        print("   Format: "+title+" --> "+FanacNames.StandardizeName(title.lower())+" --> "+str(format))

        if format == None:
            # This is actually a good thing, because it means that the fanzines has the default index.html type
            print("   Using default directory format of (0,0)/(1,1)")

            # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
            # We need to turn relPath into a URL
            url=Helpers.RelPathToURL(dirname)
            print("   '"+title+"', "+url+"'")
            if url == None:
                continue
            if url.startswith("http://www.fanac.org") and not url.startswith("http://www.fanac.org//fan_funds") and not url.startswith("http://www.fanac.org/fanzines/Miscellaneous"):
                ret=ReadAndAppendFanacFanzineIndexPage(title, url, (0, 0, None), g_fanacIssueInfo)
                if ret != None:
                    g_fanacIssueInfo=ret
            continue

        elif format == (8, 0):
            print("   Skipped because no index.html file: "+ dirname)
            continue

        # TODO: Can we move the format decision code into one function? It'sa now split between here and ReadAndAppendFanacFanzineIndexPage
        # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
        # We need to turn relPath into a URL
        url=Helpers.RelPathToURL(dirname)
        print(title, " ", url)
        if url.startswith("http://www.fanac.org") and not url.startswith("http://www.fanac.org//fan_funds"):
            ret=ReadAndAppendFanacFanzineIndexPage(title, url, format, g_fanacIssueInfo)
            if ret != None:
                g_fanacIssueInfo=ret

    # Now we have a list of all the issues of fanzines onfanac.org which have at least one 1942 issue.(Not all of the issues are 1942.)
    print("----Done reading index.html files on fanac.org")
    return

#------------------------------------------------------------------------
# This is a class which will always return the External Links table.
# It will read it the first time it is initialized and thereafter just return it.
# Usage: x=ExternalClass().List()
global g_externalLinks1942
g_externalLinks1942=[]

class ExternalLinks:
    def __init__(self):
        import collections
        global g_externalLinks1942
        if len(g_externalLinks1942) == 0:
            print("----Begin reading External Links 1942.txt")
            # Now we read Links1942.txt, which contains links to issues of fanzines *outside* fanac.org.
            # It's organized as a table, with the first row a ';'-delimited list of column headers
            #    and the remaining rows are each a ';'-delimited pointer to an exteral fanzine
            # First read the header line which names the columns.  The headers are separated from ';", so we need to remove these.
            f=open("External Links 1942.txt")
            line=f.readline()
            line=line.replace(";", "")
            links1942ColNames=line.split(" ")
            # Define a named tuple to hold the data I get from the external links input file
            # This -- elegantly -- defines a named tuple to hold the elements of a line and names each element according to the column header in the first row.
            ExternalLinksData=collections.namedtuple("ExternalLinksData", line)

            # Now read the rest of the data.
            for line in f:  # Each line after the first is a link to an external fanzine
                print("   line="+line.strip())
                temp=line.split(";")
                t2=[]
                for t in temp:
                    t2.append(t.strip())
                g_externalLinks1942.append(ExternalLinksData(*tuple(t2)))  # Turn the list into a named tuple.
            f.close()
            print("----Done reading External Links 1942.txt")

    def List(self):
        return g_externalLinks1942


#================================================================================================
# Inline function to format Stuff, which is a list of IssueSpecs
# Stuff is commonly a list of issue specification interspersed with nonce items
# For now, we'll attempt only to format what we interpret, above: whole numbers and Vol/# combinations
def FormatStuff(fz):
    if fz.issues == None or fz.issues.len() == 0:
        return fz.issuesText+" "+fz.possible+" "+fz.junk

    print("   FormatStuff: fz.name="+str(fz.title)+"  fz.fanacDirName="+str(fz.fanacDirName)+"   fz.stuff="+fz.issues.Print())

    out=""
    # Our job here is to turn this into HTML which includes links for those issues which have links.
    for issue in fz.issues.List():
        # issue is a tuple of a vol and a num.
        # If both exists, it is a Vn#n pair
        # If V is none, then num is a whole number.
        # Neither existing should never happen

        # We first look to see if fanzine-vol-issue points to a fanzine on fanac.org
        # Failing that, we look to see if it is in the External Links table
        # Failing that, we just append the plain text
        found=False
        v=None
        if issue.Vol == None and issue.Num == None and issue.Whole == None:     # We have neither Vol nor Num.  We have no issue information.
            v="(oops)"

        # We should either have a Whole (number) or a Vol+Num
        # TODO: Add support for UninterpretableText and TrailingGarbage
        elif issue.Whole != None:     # We have Num, but not Vol
            # Look up the fanzine to see if it is on fanac.org. Then look up the Vol/Issue to see if the specific issue is there.
            name = fz.fanacFanzineName or fz.title

            # Check the table of all fanzines issues on fanac.org to see if there is a match for fanzine-vol-issue
            url=None
            for fii in g_fanacIssueInfo:
                if fii.Vol != None:
                    n=fii.Number
                    w=None
                else:
                    n=None
                    w=fii.Number
                if Helpers.CompareIssueSpec(fii.FanzineName, fii.Vol, n, w, name, None, None, issue.Whole):
                    url=fii.URL
                    text=str(issue.Whole)
                    print("   FormatStuff: Found on fanac: issue="+str(issue.Whole)+"  url="+url)
                    break
            if url != None:
                garbage=""
                if issue.TrailingGarbage != None:
                    garbage=issue.TrailingGarbage
                v=Helpers.FormatLink("#"+str(issue.Whole)+garbage, Helpers.CreateFanacOrgAbsolutePath(fz.fanacDirName, url))


            # If we couldn't find anything on fanac.org, look for an external link
            if v == None:
                # We have a name, and a whole number.  See if they turn up as an external link]
                for ext in ExternalLinks().List():
                    if FanacNames.CompareNames(ext.Title, name) and int(ext.Whole_Number) == issue.Whole:
                        url=ext.URL
                        print("   FormatStuff: Found external: issue="+str(issue.Whole)+"  url="+url)
                        found=True
                        if url!=None:
                            v=Helpers.FormatLink("#"+str(issue.Whole), url)

            if v == None:
                # No luck anywhere
                v="#"+str(issue.Whole)
                print("   No luck anywhere: "+v)



        else:
            # We don't have issue.Whole, so we must have both vol and num
            # Look up the fanzine to see if it is on fanac.org. Then look up the Vol/Issue to see if the specific issue is there.
            name = fz.fanacFanzineName or fz.title

            # Check the table of all fanzines issues on fanac.org to see if there is a match for fanzine-vol-issue
            url=None
            for fii in g_fanacIssueInfo:
                if fii.Vol != None:
                    n=fii.Number
                    w=None
                else:
                    n=None
                    w=fii.Number
                if Helpers.CompareIssueSpec(fii.FanzineName, fii.Vol, n, w, name, issue.Vol, issue.Num, issue.Whole):
                    url=fii.URL
                    text=str(issue.Num)
                    print("   FormatStuff: Found on fanac: vol="+str(issue.Vol)+" issue="+str(issue.Num)+"  url="+url)
                    break
            if url != None:
                v=Helpers.FormatLink("V"+str(issue.Vol)+"#"+str(issue.Num), Helpers.CreateFanacOrgAbsolutePath(fz.fanacDirName, url))


            # If we couldn't find anything on fanac.org, look for an external link
            if v == None:
                # We have a name, and a whole number.  See if they turn up as an external link]
                for ext in ExternalLinks().List():
                    if ext.Volume != None:
                        n=fii.Number
                        w=None
                    else:
                        n=None
                        w=fii.Number
                    if Helpers.CompareIssueSpec(ext.Title, ext.Volume, n, w, name, issue.Vol, issue.Num, issue.Whole):
                        url=ext.URL
                        print("   FormatStuff: Found external: Vol="+str(issue.Vol)+" issue="+str(issue.Num)+"  url="+url)
                        if url!=None:
                            v=Helpers.FormatLink("V"+str(issue.Vol)+"#"+str(issue.Num), url)

            if v == None:
                # No luck anywhere, so no link: just text
                v="V"+str(issue.Vol)+"#"+str(issue.Num)
                print("   No luck anywhere: "+v)

        if len(out) > 0:
            out=out+", "
        if v != None:
            out=out+v
    return out

