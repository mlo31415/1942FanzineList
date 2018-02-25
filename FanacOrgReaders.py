from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames
import re
import FanacDirectoryFormats
import ExternalLinks
import FanacDirectories


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
    for key, (title, dirname) in FanacDirectories.FanacDirectories().Dict().items():
        print("'"+key+"', "+title+"', "+dirname+"'")
        if '/' in dirname:
            print("   skipped because of '/' in name:"+dirname)
            continue

        # Get the index file format for this directory
        format=FanacDirectoryFormats.FanacDirectoryFormats().GetFormat(dirname.lower())
        print("   Format: "+title+" --> "+FanacNames.StandardizeName(title.lower())+" --> "+str(format))

        if format == (8, 0):
            print("   Skipped because no index.html file: "+ dirname)
            continue

        # The URL we get is relative to the fanzines directory which has the URL fanac.org/fanzines
        # We need to turn relPath into a URL
        url=Helpers.RelPathToURL(dirname)
        print("   '"+title+"', "+url+"'")
        if url == None:
            continue
        if url.startswith("http://www.fanac.org") and not url.startswith("http://www.fanac.org//fan_funds") and not url.startswith("http://www.fanac.org/fanzines/Miscellaneous"):
            g_fanacIssueInfo=ReadAndAppendFanacFanzineIndexPage(title, url, format, g_fanacIssueInfo)

    # Now g_fanacIssueInfo is a list of all the issues of fanzines on fanac.org which have at least one 1942 issue.(Not all of the issues are 1942.)
    print("----Done reading index.html files on fanac.org")
    return


# ============================================================================================
# Function to extract information from a fanac.org fanzine index.html page
def ReadAndAppendFanacFanzineIndexPage(fanzineName, directoryUrl, format, fanzineIssueList):
    skippers=["Emu Tracks Over America", "Flight of the Kangaroo, The", "Enchanted Duplicator, The", "Tails of Fandom", "BNF of IZ", "NEOSFS Newsletter, Issue 3, The"]
    if fanzineName in skippers:
        print("   Skipping: "+fanzineName)
        return fanzineIssueList

    FanacIssueInfo=collections.namedtuple("FanacIssueInfo", "FanzineName  FanzineIssueName  Vol  Number  URL  Year")

    # We're only prepared to read a few formats.  Skip over the others right now.
    OKFormats=((1,1), (1,6))
    codes=(format[0], format[1])
    if not codes in OKFormats:
        print("      Can't handle format:"+str(format) +" from "+directoryUrl)
        return fanzineIssueList

    # Download the index.html which lists all of the issues of the specified fanzine currently on the site
    try:
        h = requests.get(directoryUrl)
    except:
        try:
            h=requests.get(directoryUrl)
        except:
            print("***Request failed for: "+directoryUrl)
            return fanzineIssueList

    s = BeautifulSoup(h.content, "html.parser")
    b = s.body.contents
    # Because the structures of the pages are so random, we need to search the body for the table.
    # *So far* all of the tables have been headed by <table border="1" cellpadding="5">, so we look for that.

    tab=Helpers.LookForTable(b)
    if tab == None:
        print("*** No Table found!")
        return fanzineIssueList

    # OK, we probably have the issue table.  Now decode it.
    # The first row is the column headers
    # Subsequent rows are fanzine issue rows

    # Some of the rows showing up in tab.contents will be tags containing only a newline -- start by compressing them out.
    tab.contents=Helpers.RemoveNewlineRows(tab.contents)

    # Create a composition of all columns. The header column may have newline eleemnts, so compress them out.
    # Then compress out sizes in the actual column header, make them into a list, and then join the list separated by spaces
    # We wind up with a string just right to be the element designator of a named tuple.
    columnHeaders=" ".join([col.string.replace(" ", "") for col in Helpers.RemoveNewlineRows(tab.contents[0])])
    print("   columnHeaders="+columnHeaders)

    # Remove some sloppy column header stuff and characters that are OK, but which can't be in Namedtuple field names
    columnHeaders=columnHeaders.replace("Vol/#", "VolNum").replace("Vol./#", "VolNum")
    columnHeaders=columnHeaders.replace("#", "Num")
    columnHeaders=columnHeaders.replace("/", "").replace("Mo.", "Month").replace("Pp.", "Pages")
    # And can you believe duplicate column headers?
    if len(columnHeaders.split(" Number "))>2:
        columnHeaders=columnHeaders.replace(" Number ", " Whole ", 1) # If Number appears twice, replace the first with Whole

    # Create the named tuple
    FanzineTable=collections.namedtuple("FanzineTable", columnHeaders)

    # The rest of the table is one or more rows, each corresponding to an issue of that fanzine.
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

    rows=InterpretFanzineTable(fanzineName, FanacIssueInfo, fanzineTable, format)

    # Now select just the issues for 1942 and append them to the fanzineIssueList
    for row in rows:
        if row.Year == 1942:
            print("      1942: ReadAndAppendFanacFanzineIndexPage: appending "+str(row))
            fanzineIssueList.append(row)

    return fanzineIssueList


# ---------------------------------------------------------
# Given a fanzine table that has been read in, go through it and generate a list of FanzineInfo rows
def InterpretFanzineTable(fanzineName, FanacIssueInfo, fanzineTable, format):
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
                if date!=None:
                    year=date.Year
        except:
            year=None  # Gotta have *some* code in the except clause

        if year==None:
            print("   ***Can't find year")
            continue

        # Now find the column containing the issue designation. It could be "Issue" or "Title"
        issueCol=None
        for i in range(0, len(row._fields)):
            if row._fields[i]=="Issue":
                issueCol=i
                break
        if issueCol==None:
            for i in range(0, len(row._fields)):
                if row._fields[i]=="Title":
                    issueCol=i
                    break
        if issueCol==None:
            print("  ***No IssueCol")
            continue

        # Now for code which depends on the index,html file format
        if format[0]==1 and format[1]==1:  # The default case

            # Get the num from the name
            name, href=Helpers.GetHrefAndTextFromTag(row[issueCol])
            if href==None:
                print("    skipping: "+name)
                continue

            p=re.compile("^.*\D([0-9]+)\s*$")
            m=p.match(name)
            num=None
            if m!=None and len(m.groups())==1:
                num=int(m.groups()[0])

            fi=FanacIssueInfo(FanzineName=fanzineName, FanzineIssueName=name, URL=href, Year=year, Vol=None, Number=num)  # (We ignore the Vol and Num for now.)
            print("   (0,0): "+str(fi))
            rows.append(fi)

        elif format[0]==1 and format[1]==6:  # The name in the title column ends in V<n>, #<n>

            # We need two things: The contents of the first (linking) column and the year.
            name, href=Helpers.GetHrefAndTextFromTag(row[issueCol])
            if href==None:
                print("    skipping: "+name)
                continue

            p=re.compile("(.*)V([0-9]+),?\s*#([0-9]+)\s*$")
            m=p.match(name)
            if m!=None and len(m.groups())==3:
                fi=FanacIssueInfo(FanzineName=fanzineName, FanzineIssueName=name, URL=href, Year=year, Vol=int(m.groups()[1]), Number=int(m.groups()[2]))
                print("   (1,6): "+str(fi))
                rows.append(fi)
    return rows


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
            v=issue.UninterpretableText

        # We should either have a Whole (number) or a Vol+Num
        # TODO: Add support for UninterpretableText and TrailingGarbage
        elif issue.Whole != None:     # We have Num, but not Vol
            # Look up the fanzine to see if it is on fanac.org. Then look up the Vol/Issue to see if the specific issue is there.
            name = fz.fanacFanzineName or fz.title
            garbage=""
            if issue.TrailingGarbage!=None:
                garbage=issue.TrailingGarbage

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
                v=Helpers.FormatLink("#"+str(issue.Whole)+garbage, Helpers.CreateFanacOrgAbsolutePath(fz.fanacDirName, url))


            # If we couldn't find anything on fanac.org, look for an external link
            if v == None:
                # We have a name, and a whole number.  See if they turn up as an external link]
                for ext in ExternalLinks.ExternalLinks().List():
                    if FanacNames.CompareNames(ext.Title, name) and int(ext.Whole_Number) == issue.Whole:
                        url=ext.URL
                        print("   FormatStuff: Found external: issue="+str(issue.Whole)+"  url="+url)
                        found=True
                        if url!=None:
                            v=Helpers.FormatLink("#"+str(issue.Whole)+garbage, url)

            if v == None:
                # No luck anywhere
                v="#"+str(issue.Whole)+garbage
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
                for ext in ExternalLinks.ExternalLinks().List():
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

