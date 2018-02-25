import collections
import Helpers
import re

# This is a tuple which associates all the different forms of a fanzine's name on fanac.org.
# It does *not* try to deal with namechanges!
#   JoeName is the name used by Joe in his database (e.g., 1942fanzines.pdf on fanac.org)
#   DisplayName is the name we prefer to use for people-readable materials
#   FanacStandardName is the human-readable name used in the big indexes under modern and classic fanzines
#   RetroNsame is the named used in the Retro_Hugos.html file on fanac.org
FanacName=collections.namedtuple("FanacName", "JoesName, DisplayName, FanacStandardName, RetroName")

global g_fanacNameTuples  # Holds all the accumulated name tuples
g_fanacNameTuples=[]

# We will build up a list of these tuples with one or more access functions so that the appropriate tuple can be easily found
# (Basically functions which make it act like a dictionary with multiple keys for each tuple.)

#======================================================================================
# Do a case-insenstive compare which also treates "The xxx" and "xxx, The" as the same
def CompareNames(name1, name2):
    if name1 == None or name2 == None:
        return False

    if name1.lower().startswith("the "):
        name1=name1[4:]+", the"
        name1=name1.strip()

    if name2.lower().startswith("the "):
        name2=name2[4:]+", the"
        name2=name2.strip()

    if name1.lower().startswith("a "):
        name1=name1[2:]+", a"
        name1=name1.strip()

    if name2.lower().startswith("a "):
        name2=name2[2:]+", a"
        name2=name2.strip()

    if name1.lower().startswith("an "):
        name1=name1[3:]+", an"
        name1=name1.strip()

    if name2.lower().startswith("an "):
        name2=name2[3:]+", an"
        name2=name2.strip()

    return Helpers.CompressName(name1) == Helpers.CompressName(name2)


#======================================================================
# Given a Retro_Name create a new tuple if needed or add it to an existing tuple
def AddRetroName(name):
    if len(g_fanacNameTuples)> 0:
        for t in g_fanacNameTuples:
            if t.RetroName == name:
                return  # Nothing to do -- it's already in there.

    # Now we check to see if a matching name is in it that has a blank RetroName.
    for i in range(0, len(g_fanacNameTuples)):
        if CompareNames(g_fanacNameTuples[i].FanacStandardName, name):
            g_fanacNameTuples[i]=g_fanacNameTuples[i]._replace(RetroName=name)
            return

    # Nothing. So the last recoruse is simply to add a new tuple.
    g_fanacNameTuples.append(FanacName(JoesName=None, FanacStandardName=None, DisplayName=None, RetroName=name))
    return


#========================================================
# Add the fanac directory dictionary to the names list
#
def AddFanacDirectories(fanacDirs):
    if fanacDirs == None or len(fanacDirs) == 0:
        print("***AddFanacDirectories tried to add an empty FanacOrgReaders.fanacDirectories")
        return

    # This is being done to initialize fanacNameTuples, so make sure it';s empty
    if g_fanacNameTuples != None and len(g_fanacNameTuples) > 0:
        print("***AddFanacDirectories tried to initialize an non-empty fanacNameTuples")
        return

    for name, dir in fanacDirs.items():
        g_fanacNameTuples.append(FanacName(JoesName=None, DisplayName=None, FanacStandardName=name, RetroName=None))

    return


#=====================================================================
# This checks for an exact match of the Fanac Standard name
def ExistsFanacStandardName(name):
    for nt in g_fanacNameTuples:
        if nt.FanacStandardName.lower() == name.lower():
            return True
    return False


#=====================================================================
# This checks for an exact match of the Fanac Standard name
def LocateFanacStandardName(name):
    for i in range(0, len(g_fanacNameTuples)):
        if g_fanacNameTuples[i].FanacStandardName.lower() == name.lower():
            return i
    return None


#=======================================================================
def AddJoesName(jname):
    # Joe's name may have case oddities or may be reversed ("xxx, The" rather than "The xxx") or something
    # Add Joe's name to the master list.
    # It will either match an existing entry or create a new entry

    i=LocateFanacStandardName(jname)
    if i != None:
        g_fanacNameTuples[i]=g_fanacNameTuples[i]._replace(JoesName=jname)
        return

    # Try moving a leading "The " to the end
    # TODO: use the names class to deal with this
    if jname.lower().startswith("the "):
        i=LocateFanacStandardName(jname[4:]+", The")
        if i != None:
            g_fanacNameTuples[i]=g_fanacNameTuples[i]._replace(JoesName=jname)
            return

    # Try adding a trailing ", the" since sometimes Joe's list omits this
    i=LocateFanacStandardName(jname+", the")
    if i!= None:
        g_fanacNameTuples[i]=g_fanacNameTuples[i]._replace(JoesName=jname)
        return

    # If none of this works, add a new entry
    # Deal with a potential leading "The "
    if jname.lower().startswith("the "):
        g_fanacNameTuples.append(FanacName(JoesName=jname, DisplayName=None, FanacStandardName=jname+", The", RetroName=None))
        return

    # Just add it as-is
    g_fanacNameTuples.append(FanacName(JoesName=jname, DisplayName=None, FanacStandardName=jname, RetroName=None))


#======================================================================
# Given a Fanac Standard fanzine name create a new tuple if needed or add it to an existing tuple
def AddFanzineStandardName(name):
    #
    # if len(fanacNameTuples) == 0:
    #     fanacNameTuples=FanacName(None, None, None, name, None)
    #     return fanacNameTuples

    for t in g_fanacNameTuples:
        if t.FanacStandardName == name:
           return g_fanacNameTuples

    g_fanacNameTuples.append(FanacName(JoesName=None, DisplayName=None, FanacStandardName=name, RetroName=None))
    return


#==========================================================================
# Convert a name to standard by lookup
def StandardizeName(name):

    # First handle the location of the "The"
    if name[0:3] == "The ":
        name=name[4:]+", The"

    # First see if it is in the list of standard names
    for nt in g_fanacNameTuples:
        if nt.FanacStandardName != None and Helpers.CompareCompressedName(nt.FanacStandardName, name):
            return nt.FanacStandardName

    # Now check other forms.
    for nt in g_fanacNameTuples:
        if nt.RetroName != None and Helpers.CompareCompressedName(nt.RetroName, name):
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in g_fanacNameTuples:
        if nt.JoesName != None and Helpers.CompareCompressedName(nt.JoesName, name):
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in g_fanacNameTuples:
        if nt.DisplayName != None and Helpers.CompareCompressedName(nt.DisplayName, name):
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"
    return "StandardizeName("+name+") failed"


class IssueSpec:

    def __init__(self):
        self.Vol=None
        self.Num=None
        self.Whole=None
        self.UninterpretableText=None   # Ok, I give up.  Just hold the text as text.
        self.TrailingGarbage=None       # The uninterpretable stuff following the interpretable spec held in this instance

    def Set2(self, v, n):
        self.Vol=v
        self.Num=n
        return self

    def Set1(self, w):
        self.Whole=w
        return self

    def SetUninterpretableText(self, str):
        self.UninterpretableText=str
        return self

    def SetTrailingGarbage(self, str):
        self.TrailingGarbage=str
        return self

    def Print(self):
        if self.UninterpretableText != None:
            return "IS("+self.UninterpretableText+")"

        v="-"
        if self.Vol != None:
            v=str(self.Vol)
        n="-"
        if self.Num != None:
            n=str(self.Num)
        w="-"
        if self.Whole != None:
            w=str(self.Whole)

        s="IS(V"+v+", N"+n+", W"+w
        if self.TrailingGarbage != None:
            s=s+", "+self.TrailingGarbage
        return s+")"


class IssueSpecList:
    def __init__(self):
        self.list=[]

    def Append1(self, issuespec):
        self.list.append(issuespec)

    def Append2(self, vol, issuelist):
        for i in issuelist:
            self.Append(IssueSpec().Set2(vol, i))

    def Append(self, isl):
        self.list.extend(isl)

    def Print(self):
        s=""
        for i in self.list:
            if len(s) > 0:
                s=s+", "
            if i != None:
                s=s+i.Print()
            else:
                s=s+"Missing ISlist"
        if len(s) == 0:
            s="Empty ISlist"
        return s

    def len(self):
        return len(self.list)

    def List(self):
        return self.list


# -------------------------------------------------------------------------------
# This takes one issue text string (which may specify multiple issues) and interpret it.
def InterpretVolNumSpecText(specStr):
    # OK, now try to decode the spec and return a list (possibly of length 1) of IssueSpecs
    # It could be
    #   Vnn#nn
    #   Vnn:nn
    #   Vnn#nn,nn,nn
    #   Vnn:nn,nn,nn

    try:
        # First split the Volume and Number parts on the '#' or ':'
        loc=specStr.find("#")
        if loc == -1:
            loc=specStr.find(":")

        # Do we have a volume+number-type spec?
        if loc != -1:
            vstr=specStr[1:loc]  # Remove the 'V'
            vol=int(vstr)

            nstr=specStr[loc+1:]
            # This could be either a single number or a comma-separated string of numbers
            nlist=nstr.split(",")
            if len(nlist) == -1:
                num=int(nlist)
                return [IssueSpec().Set2(vol, num)]
            else:
                isl=[]
                for n in nlist:
                    isl.append(IssueSpec().Set2(vol, int(n)))
                return isl

        # OK, since there was no delimiter, we have a single issue number
        return [IssueSpec().Set1(int(specStr))]

    except:
        print("oops: "+specStr)
        return None


# This takes one issue text string (which may specify multiple issues) and interpret it.
def InterpretWholenumSpecText(specStr):
    # OK, now try to decode the spec and return a list (possibly of length 1) of IssueSpecs
    # Since this is a Whole number, the format is simple, but we need to deal with decorations, e.g, '4?"

    specStr=specStr.strip()
    if len(specStr) == 0:
        return None

    isAllDigits=all([x.isdigit() for x in specStr])  # Isn't this cute? Comprehension creates list of logical from test of isdigit() on each character, and all() does an and of them all

    if isAllDigits:
        try:
            return [IssueSpec().Set1(int(specStr))]
        except:
            return [IssueSpec()]

    # OK, we have some non-digits in here.
    # For now, let's deal with the case where the leading digits are all we care about
    p=re.compile("^(\d+)(.*)$")
    m=p.match(specStr)
    if m!=None and len(m.groups()) == 2:
        ispeclist=InterpretWholenumSpecText(m.groups()[0])
        ispeclist[0].SetTrailingGarbage(m.groups()[1])
        return ispeclist

    print("oops: "+specStr)
    return None

# ----------------------------------------------------------
# Take a fanzine title string and try to capitalize it correctly
def CapitalizeFanzine(name):

    # Start by putting the name in title case.
    name=name.title()

    # Now de-capitalize some words
    name=name.replace(" Of ", " of ").replace(" The ", " the ").replace(" In ", " in ").replace( "And ", " and ")

    # Deal with an odd limitation of title() where it leaves possessive 'S capitalized (e.g., "Milty'S Mag")
    name=name.replace("'S ", "'s ").replace("’S ", "’s ")

    return name