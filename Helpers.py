import os
from bs4 import NavigableString
import FanacNames
from datetime import datetime
import timestring as timestring

#-----------------------------------------
# Find text bracketed by <b>...</b>
# Return the contents of the first pair of brackets found and the remainder of the input string
def FindBracketedText(s, b):
    strlower=s.lower()
    l1=strlower.find("<"+b.lower())
    if l1 == -1:
        return "", ""
    l1=strlower.find(">", l1)
    if l1 == -1:
        print("***Error: no terminating '>' found in "+strlower+"'")
        return "", ""
    l2=strlower.find("</"+b.lower()+">", l1+1)
    if l2 == -1:
        return "", ""
    return s[l1+1:l2], s[l2+3+len(b):]

#-------------------------------------
# Function to pull and hfref and accompanying text from a Tag
# The structure is "<a href='URL'>LINKTEXT</a>
# We want to extract the URL and LINKTEXT
def GetHrefAndTextFromTag(tag):
    try:
        href=tag.contents[0].attrs.get("href", None)
    except:
        try:
            href=tag.attrs.get("href")
        except:
            return tag, None

    return (tag.contents[0].string, href)

#-----------------------------------------
# Function to generate the proper kind of path.  (This may change depending on the target location of the output.)
def RelPathToURL(relPath):
    if relPath == None:
        return None
    if relPath.startswith("http"):  # We don't want to mess with foreign URLs
        return None
    return "http://www.fanac.org/"+os.path.normpath(os.path.join("fanzines", relPath)).replace("\\", "/")


#-----------------------------------------
# Simple function to name tags for debugging purposes
def N(tag):
    try:
        return tag.__class__.__name__
    except:
        return "Something"

#----------------------------------------
# Function to compress newline elements from a list of Tags.
def RemoveNewlineRows(tags):
    compressedTags = []
    for row in tags:
        if not isinstance(row, NavigableString):
            compressedTags.append(row)
    return compressedTags

#---------------------------------------
# Function to find the index of a string in a list of strings
def FindIndexOfStringInList(list, str):
    for i in range(0, len(list) - 1):
        if list[i] == str:
            return i

#--------------------------------------------
# Function to attempt to decode an issue designation into a volume and number
# Return a tuple of Volume and Number
# If there's no volume specified, Volume is None and Number is the whole number
# If we can't make sense of it, return (None, None), so if the 2nd member of the tuple is None, conversion failed.
def DecodeIssueDesignation(str):
    try:
        return (None, int(str))
    except:
        i=0  # A dummy statement since all we want to do with an exception is move on to the next option.

    # Ok, it's not a simple number.  Drop leading and trailing spaces and see if it of the form #nn
    s=str.strip().lower()
    if len(s) == 0:
        return (None, None)
    if s[0] == "#":
        s=s[1:]
        if len(s) == 0:
            return (None, None)
        try:
            return (None, int(s))
        except:
            i=0 # A dummy statement since all we want to do with an exception is move on to the next option.

    # This exhausts the single number possibilities
    # Maybe it's of the form Vnn, #nn (or Vnn.nn or Vnn,#nn)

    # Strip any leading 'v'
    if len(s) == 0:
        return (None, None)
    if s[0] == "v":
        s=s[1:]
        if len(s) == 0:
            return (None, None)

    # The first step is to see if there's at least one of the characters ' ', '.', and '#' in the middle
    # We split the string in two by a span of " .#"
    # Walk through the string until we;ve passed the first span of digits.  Then look for a span of " .#". The look for at least one more digit.
    # Since we've dropped any leading 'v', we kno we must be of the form nn< .#>nnn
    # So if the first character is not a digit, we give up.
    if not s[0].isdigit():
        return (None, None)

    # Now, the only legetimate charcater other than digits are the three delimiters, so translate them all to blanks and then split into the two digit strings
    spl=s.replace(".", " ").replace("#", " ").split()
    if len(spl) != 2:
        return (None, None)
    try:
        return (int(spl[0]), int(spl[1]))
    except:
        return (None, None)


# ----------------------------------------
# Function to search recursively for the table containing the fanzines listing
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


#==================================================================================
def CreateFanacOrgAbsolutePath(fanacDir, str):
    return "http://www.fanac.org/fanzines/"+fanacDir+"/"+str


#==================================================================================
# Return a properly formatted link
def FormatLink(name, url):
    # TODO: Do we need to deal with tgurning blanks into %20 whatsits?
    return '<a href='+url+'>'+name+'</a>'


#==================================================================================
# Compare a filename, volume and number with a second set
def CompareIssueSpec(name1, vol1, num1, whole1, name2, vol2, num2, whole2):
    if not FanacNames.FanacNames().CompareNames(name1, name2):
        return False

    # Sometimes we pass in integers and sometimes strings.  Let's work with strings here
    if vol1 is not None:
        vol1=str(vol1)
    if num1 is not None:
        num1=str(num1)
    if vol2 is not None:
        vol2=str(vol2)
    if num2 is not None:
        num2=str(num2)
    if whole1 is not None:
        whole1=str(whole1)
    if whole2 is not None:
        whole2=str(whole2)

    # The strategy is to allow over-specification (e.g., both Vol+Num and WholeNum.
    # So one or the other must match
    if vol1 != None and num1 != None and vol1 == vol2 and num1 == num2:
        return True
    if whole1 != None and whole1 == whole2:
        return True

    # A Onesie should have all the numbers None or empty string
    if (vol1 is None or vol1 == "")\
            and (vol2 is None or vol2 == "")\
            and (num1 is None or num1 == "")\
            and (num2 is None or num2 == "")\
            and (whole1 is None or whole1 == "")\
            and (whole2 is None or whole2 == ""):
        return True

    return False

#==================================================================================
# Create a name for comparison purposes which is lower case and without whitespace or punctuation
# We make it all lower case
# We move leading "The ", "A " and "An " to the rear
# We remove spaces and certain punctuation
def CompressName(name):
    name=name.lower()
    if name.startswith("the "):
        name=name[:4]+"the"
    if name.startswith("a "):
        name=name[:2]+"a"
    if name.startswith("an "):
        name=name[:3]+"an"
    return name.replace(" ", "").replace(",", "").replace("-", "").replace("'", "").replace(".", "").replace("’", "")


#==================================================================================
def CompareCompressedName(n1, n2):
    return CompressName(n1) == CompressName(n2)


# ===================================================================
# Date-Time stuff

# ----------------------------------------
# Remove certain strings which amount to whitespace
def RemoveDebris(str):
    return str.replace("<br>", "").replace("<BR>", "")

# ----------------------------------------
def InterpretYear(yearstring):
    yearstring=RemoveDebris(yearstring)
    if len(yearstring) == 0:
        return None
    try:
        year=int(yearstring)
    except:
        print("   ***Year conversion failed: '" + yearstring+"'")
        year=None
    return year


# ----------------------------------------
def InterpretDay(daystring):
    daystring=RemoveDebris(daystring)
    if len(daystring) == 0:
        return None
    try:
        day=int(daystring)
    except:
        print("   ***Day conversion failed: '" + daystring+"'")
        day=None
    return day


# ----------------------------------------
def InterpretMonth(monthstring):
    monthstring=RemoveDebris(monthstring)
    if len(monthstring) == 0:
        return None
    monthConversionTable={"jan" : 1, "january" : 1, "1" : 1,
                          "feb" : 2, "february" : 2, "2" : 2,
                          "mar" : 3, "march" : 3, "3" : 3,
                          "apr" : 4, "april" : 4, "4" : 4,
                          "may" : 5, "5" : 5,
                          "jun" : 6, "june" : 6, "6" : 6,
                          "jul" : 7, "july" : 7, "7" : 7,
                          "aug" : 8, "august" : 8, "8" : 8,
                          "sep" : 9, "sept" : 9, "september" : 9, "9" : 9,
                          "oct" : 10, "october" : 10, "10" : 10,
                          "nov" : 11, "november" : 11, "11" : 11,
                          "dec" : 12, "december" : 12, "12" : 12,
                          "1q" : 1,
                          "4q" : 4,
                          "7q" : 7,
                          "10q" : 10,
                          "spring" : 4,
                          "summer" : 7,
                          "fall" : 10, "autumn" : 10,
                          "winter" : 1,
                          "january-february" : 2,
                          "march-april" : 4,
                          "april-may" : 5,
                          "apr-may" : 5,
                          "may-june" : 6,
                          "july-august" : 8,
                          "august-september" : 9,
                          "september-october" : 10,
                          "sep-oct" : 10,
                          "october-november" : 11,
                          "oct-nov" : 11,
                          "september-december" : 12,
                          "november-december" : 12,
                          "december-january" : 12,
                          "dec-jan" : 12}
    try:
        month=monthConversionTable[monthstring.replace(" ", "").lower()]
    except:
        print("   ***Month conversion failed: "+monthstring)
        month=None
    return month

# ----------------------------------------
# Interpret a free-form date string
# We will assume no time information
def InterpretDateString(datestring):
    # We will try a series of possible formats
    try:
        return timestring.date(datestring)
    except:
        pass

    try:
        return int(datestring)  # Just a bare number.  It pretty much has to be a year.
    except:
        pass

    try:
        return datetime.strptime(datestring, '%b %Y')   # 'Jun 2005'
    except:
        pass

    try:
        return datetime.strptime(datestring, '%B %Y')   # 'June 2005'
    except:
        pass

    try:
        # Look at the case of exactly two tokens, and the second is a year-like number (E.g., June 1987)
        d=datestring.split(" ")
        try:
            y=int(d[1])
            m=InterpretMonth(d[0])
            return datetime(y, m, 1)
        except:
            pass
    except:
        pass
    return None


# ----------------------------------------
def CannonicizeColumnHeaders(header):
    # 2nd item is the cannonical form
    translationTable={"title" : "title",
                      "issue" : "issue",
                      "month" : "month",
                      "mo." : "month",
                      "day" : "day",
                      "year" : "year",
                      "repro" : "repro",
                      "editor" : "editor",
                      "editors" : "editor",
                      "notes" : "notes",
                      "pages" : "pages",
                      "page" : "pages",
                      "size" : "size",
                      "type" : "type",
                      "#" : "#",
                      "no" : "#",
                      "number" : "#",
                      "vol" : "vol",
                      "volume" : "vol",
                      "num" : "num",
                      "headline" : "headline",
                      "publisher" : "publisher",
                      "published" : "date"}
    try:
        return translationTable[header.replace(" ", "").lower()]
    except:
        print("   ***Column Header conversion failed: '" + header + "'")
        return None
