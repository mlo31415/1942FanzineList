import os
from bs4 import NavigableString
import FanacNames


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
        href=tag.attrs.get("href")

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
# Compare a filename, volume and number woith a second set
def CompareIssueSpec(name1, vol1, num1, name2, vol2, num2):
    if not FanacNames.CompareNames(name1, name2):
        return False
    if (vol1 == None and vol2 != None) or (vol1 != None and vol2 == None):
        return False
    if vol1 != vol2:
        return False
    if num1 != num2:
        return False
    return True

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