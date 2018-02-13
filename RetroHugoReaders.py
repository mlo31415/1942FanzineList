from bs4 import BeautifulSoup
import requests
import collections
import Helpers
import FanacNames

# ============================================================================================
# Read the 1942 All Fanzine list and extract all the names and add them to the fanacNameTuples list
# All we want to do here is extract the fanzines names and add them to the list of named tuples.
def Read1942FanzineList():
    print("----Begin reading Joe's 1942 Fanzine List.txt")

    # Define a named tuple to hold the data I get from Joe's input file
    JoesData=collections.namedtuple("JoesData", "Name Editor Stuff")

    # OK, next we open the complete list of 1942 fanzines from Joe Siclari.
    # Each line follows a vague pattern:
    # <title> '(' <name of editor(s) ')' <a usually comma-separated list of issues> <crap, frequently in parenthesis>
    # Store the parsed information in a list of tuples
    f=open("1942 All Fanzines List.txt")
    allFanzines1942=[]
    for line in f:  # Each line is a fanzine
        if line[-1:]=="\n":  # Drop the trailing newline
            line=line[:-1]
        temp="".join(line.split())  # This is a Python idiom which removes whitespace from a string
        if len(temp)==0:  # Ignore lines that are all whitespace
            continue

        loc1=line.find("(")
        if loc1==-1:
            print("*** Could find opening '(' in '"+line+"'")
            continue

        loc2=line.find(")", loc1)
        if loc2==-1:
            print("*** Could find closing ')' in '"+line+"'")
            continue

        allFanzines1942.append(JoesData(line[:loc1-1], line[loc1+1:loc2].title(), line[loc2+1:]))
        FanacNames.AddJoesName(line[:loc1-1])


    f.close()
    print("---fanzines1942 list created with "+str(len(allFanzines1942))+" elements")
    print("----Done reading Joe's 1942 Fanzine List.txt")
    return allFanzines1942


#=================================================================================
# Download the fanac.org webpage which lists all of the 1942 fanzine issues currently on the site
def ReadRetro_HugosTxtFile():

    print("----Begin reading Retro_Hugos.html file")
    h=requests.get("http://www.fanac.org/fanzines/Retro_Hugos.html")
    s=BeautifulSoup(h.content, "html.parser")
    table=s.body.ol.contents
    # The structure of the table is
    #       A string "\n"
    #       A <li> tag containing the editor's name
    #       A <ul> tag containing one or more lines of fanzines
    #       A <br/> tag
    # All we care about is the <ul> tag, which we need to decode to find individual fanzines.
    # Loop over the tags to find entries
    listOf1942FanzinesOnFanac=dict()  # This is a dictionary with the fanzine name as the key and values of linktext and URL
    for tag in table:
        if tag.name!="ul":
            continue
        line=tag.contents

        # The line is a list of tags and strings. Ignore the strings
        for tag2 in line:
            if tag2.string!=None:
                continue

            # Now we have a single fanzine entry. It has the format <li><a...></li>. We want the <a...> part
            # This is the first member of the tag's contents list.
            a=tag2.contents[0]
            hrefLinkText, hrefUrl=Helpers.GetHrefAndTextFromTag(a)
            listOf1942FanzinesOnFanac[hrefLinkText.lower()]=(hrefLinkText, hrefUrl)
            FanacNames.AddRetroName(hrefLinkText)

    print("----Done reading Retro_Hugos.html file")
    return listOf1942FanzinesOnFanac

#============================================================================================
def ReadLinks1942Txt():
    print("----Begin reading Links1942.txt")
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
        externalLinks1942.append(ExternalLinksData(*tuple(t2)))  # Turn the list into a named tuple.
    f.close()
    print("----Done reading Links1942.txt")
    return externalLinks1942
