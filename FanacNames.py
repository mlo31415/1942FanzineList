import collections
import Helpers

# This is a tuple which associates all the different forms of a fanzine's name on fanac.org.
# It does *not* try to deal with namechanges!
#   JoeName is the name used by Joe in his database (e.g., 1942fanzines.pdf on fanac.org)
#   DisplayName is the name we prefer to use for people-readable materials
#   FanacStandardName is the human-readable name used in the big indexes under modern and classic fanzines
#   RetroNsame is the named used in the Retro_Hugos.html file on fanac.org
FanacName=collections.namedtuple("FanacName", "JoesName, DisplayName, FanacStandardName, RetroName")

global fanacNameTuples  # Holds all the accumulated name tuples
fanacNameTuples=[]

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

    return Helpers.CompressName(name1) == Helpers.CompressName(name2)


#======================================================================
# Given a Retro_Name create a new tuple if needed or add it to an existing tuple
def AddRetroName(name):
    if len(fanacNameTuples)> 0:
        for t in fanacNameTuples:
            if t.RetroName == name:
                return  # Nothing to do -- it's already in there.

    # Now we check to see if a matching name is in it that has a blank RetroName.
    for i in range(0, len(fanacNameTuples)):
        if CompareNames(fanacNameTuples[i].FanacStandardName, name):
            fanacNameTuples[i]=fanacNameTuples[i]._replace(RetroName=name)
            return

    # Nothing. So the last recoruse is simply to add a new tuple.
    fanacNameTuples.append(FanacName(JoesName=None, FanacStandardName=None, DisplayName=None, RetroName=name))
    return


#========================================================
# Add the fanac directory dictionary to the names list
#
def AddFanacDirectories(fanacDirs):
    if fanacDirs == None or fanacDirs.len == 0:
        print("***AddFanacDirectories tried to add an empty FanacOrgReaders.fanacDirectories")
        return

    # This is being done to initialize fanacNameTuples, so make sure it';s empty
    if fanacNameTuples != None and len(fanacNameTuples) > 0:
        print("***AddFanacDirectories tried to initialize an non-empty fanacNameTuples")
        return

    for name, dir in fanacDirs.Dict().items():
        fanacNameTuples.append(FanacName(JoesName=None, DisplayName=None, FanacStandardName=name, RetroName=None))

    return


#=====================================================================
# This checks for an exact match of the Fanac Standard name
def ExistsFanacStandardName(name):
    for nt in fanacNameTuples:
        if nt.FanacStandardName.lower() == name.lower():
            return True
    return False


#=====================================================================
# This checks for an exact match of the Fanac Standard name
def LocateFanacStandardName(name):
    for i in range(0, len(fanacNameTuples)):
        if fanacNameTuples[i].FanacStandardName.lower() == name.lower():
            return i
    return None


#=======================================================================
def AddJoesName(jname):
    # Joe's name may have case oddities or may be reversed ("xxx, The" rather than "The xxx") or something
    # Add Joe's name to the master list.
    # It will either match an existing entry or create a new entry

    i=LocateFanacStandardName(jname)
    if i != None:
        fanacNameTuples[i]=fanacNameTuples[i]._replace(JoesName=jname)
        return

    # Try moving a leading "The " to the end
    if jname.lower().startswith("the "):
        i=LocateFanacStandardName(jname[4:]+", The")
        if i != None:
            fanacNameTuples[i]=fanacNameTuples[i]._replace(JoesName=jname)
            return

    # Try adding a trailing ", the" since sometimes Joe's list omits this
    i=LocateFanacStandardName(jname+", the")
    if i!= None:
        fanacNameTuples[i]=fanacNameTuples[i]._replace(JoesName=jname)
        return

    # If none of this works, add a new entry
    # Deal with a potential leading "The "
    if jname.lower().startswith("the "):
        fanacNameTuples.append(FanacName(JoesName=jname, DisplayName=None, FanacStandardName=jname+", The", RetroName=None))
        return

    # Just add it as-is
    fanacNameTuples.append(FanacName(JoesName=jname, DisplayName=None, FanacStandardName=jname, RetroName=None))


#======================================================================
# Given a Fanac Standard fanzine name create a new tuple if needed or add it to an existing tuple
def AddFanzineStandardName(name):
    #
    # if len(fanacNameTuples) == 0:
    #     fanacNameTuples=FanacName(None, None, None, name, None)
    #     return fanacNameTuples

    for t in fanacNameTuples:
        if t.FanacStandardName == name:
           return fanacNameTuples

    fanacNameTuples.append(FanacName(JoesName=None, DisplayName=None, FanacStandardName=name, RetroName=None))
    return


#==========================================================================
# Convert a name to standard by lookup
def StandardizeName(name):

    # First handle the location of the "The"
    if name[0:3] == "The ":
        name=name[4:]+", The"

    # First see if it is in the list of standard names
    for nt in fanacNameTuples:
        if nt.FanacStandardName != None and Helpers.CompareCompressedName(nt.FanacStandardName, name):
            return nt.FanacStandardName

    # Now check other forms.
    for nt in fanacNameTuples:
        if nt.RetroName != None and Helpers.CompareCompressedName(nt.RetroName, name):
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in fanacNameTuples:
        if nt.JoesName != None and Helpers.CompareCompressedName(nt.JoesName, name):
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in fanacNameTuples:
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

    def Set2(self, v, n):
        self.Vol=v
        self.Num=n
        return self

    def Set1(self, w):
        self.Whole=w
        return self

    def Print(self):
        v="-"
        if self.Vol != None:
            v=str(self.Vol)
        n="-"
        if self.Num != None:
            n=str(self.Num)
        w="-"
        if self.Whole != None:
            w=str(self.Whole)

        return "IS(V"+v+", N"+n+", W"+w+")"


class IssueSpecList:
    def __init__(self):
        self.list=[]

    def Append1(self, issuespec):
        self.list.append(issuespec)

    def Append2(self, vol, issuelist):
        for i in issuelist:
            self.Append(self, IssueSpec(vol, i))

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

# This takes one issue text string (which may specify multiple issues) and interpret it.
def InterpretIssueSpecText(specStr):
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
        print("oops.")
        return None
