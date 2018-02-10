import os
from bs4 import NavigableString

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
# Inline definition of a function to pull and hfref and accompanying text from a Tag
# The structure is "<a href='URL'>LINKTEXT</a>
# We want to extract the URL and LINKTEXT
def GetHrefAndTextFromTag(tag):
    try:
        href=tag.contents[0].attrs.get("href", None)
    except:
        href=tag.attrs.get("href")

    return (tag.contents[0].string, href)
# -------------------------------------

#-----------------------------------------
# Inline defintion of function to generate the proper kind of path.  (This may change depending on the target location of the output.)
def RelPathToURL(relPath):
    if relPath == None:
        return None
    if relPath[0] == ".":
        return "http://www.fanac.org/"+os.path.normpath(os.path.join("fanzines", relPath)).replace("\\", "/")
    return relPath
#-----------------------------------------


#-----------------------------------------
# Define inline a simple function to name tags for debugging purposes
def N(tag):
    try:
        return tag.__class__.__name__
    except:
        return "Something"
#-----------------------------------------

#----------------------------------------
# Inline definition of a function to compress newline elements from a list of Tags.
def RemoveNewlineRows(tags):
    compressedTags = []
    for row in tags:
        if not isinstance(row, NavigableString):
            compressedTags.append(row)
    return compressedTags
#----------------------------------------

#---------------------------------------
# Inline definition of a function to find the index of a string in a list of strings
def FindIndexOfStringInList(list, str):
    for i in range(0, len(list) - 1):
        if list[i] == str:
            return i
#---------------------------------------