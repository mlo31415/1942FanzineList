import collections

# This is a tuple which associates all the different forms of a fanzine's name on fanac.org.
# It does *not* try to deal with namechanges!
#   FanacDirName is the name of the directory under fanac.org/fanzines
#   JoeName is the name used by Joe in his database (e.g., 1942fanzines.pdf on fanac.org)
#   DisplayName is the name we prefer to use for people-readable materials
#   FanacStandardName is the human-readable name used in the big indexes under modern and classic fanzines
#   RetroNsame is the named used in the Retro_Hugos.html file on fanac.org
FanacName=collections.namedtuple("FanacName", "FanacDirName, JoesName, DisplayName, FanacStandardName, RetroName")

global fanacNameTuples  # Holds all the accumulated name tuples
fanacNameTuples=[]

# We will build up a list of these tuples with one or more access functions so that the appropriate tuple can be easily found
# (Basically functions which make it act like a dictionary with multiple keys for each tuple.)

#======================================================================================
# Do a case-insenstive compare which also treates "The xxx" and "xxx, The" as the same
def CompareNames(name1, name2):
    if name1 == None or name2 == None:
        return False

    name1=name1.lower()
    name2=name2.lower()

    if name1.startswith("the "):
        name1=name1[4:]+", the"

    if name2.startswith("the "):
        name2=name2[4:]+", the"

    return name1 == name2


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
            fanacNameTuples[i]._replace(RetroName=name)
            return

    # Nothing. So the last recoruse is simply to add a new tuple.
    fanacNameTuples.append(FanacName(FanacDirName=None, JoesName=None, FanacStandardName=None, DisplayName=None, RetroName=name))
    return


#========================================================
# Add the fanac directory dictionary to the names list
#
def AddFanacDirectories(fanacDirs):
    if fanacDirs == None or len(fanacDirs) == 0:
        print("***AddFanacDirectories tried to add an empty FanacOrgReaders.fanacDirectories")
        return

    # This is being done to initialize fanacNameTuples, so make sure it';s empty
    if fanacNameTuples != None and len(fanacNameTuples) > 0:
        print("***AddFanacDirectories tried to initialize an non-empty fanacNameTuples")
        return

    for name, dir in fanacDirs.items():
        fanacNameTuples.append(FanacName(FanacDirName=dir, JoesName=None, DisplayName=None, FanacStandardName=name, RetroName=None))

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

    i=ExistsFanacStandardName(jname)
    if i != None:
        fanacNameTuples[i]._replace(JoesName=jname)
        return

    # Try moving a leading "The " to the end
    if jname.lower.startswith("the "):
        i=ExistsFanacStandardName(jname[4:]+", The")
        if i != None:
            fanacNameTuples[i]._replace(JoesName=jname)
            return

    # Try adding a trailing ", the" since sometimes Joe's list omits this
    i=ExistsFanacStandardName(jname+", the")
    if i!= None:
        fanacNameTuples[i]._replace(JoesName=jname)
        return

    # If none of this works, add a new entry
    # Deal with a potential leading "The "
    if jname.lower.startswith("the "):
        fanacNameTuples.append(FanacName(FanacDirName=None, JoesName=jname, DisplayName=None, FanacStandardName=jname+", The", RetroName=None))
        return

    # Just add it as-is
    fanacNameTuples.append(FanacName(FanacDirName=None, JoesName=jname, DisplayName=None, FanacStandardName=jname, RetroName=None))


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

    fanacNameTuples.append(FanacName(FanacDirName=None, JoesName=None, DisplayName=None, FanacStandardName=name, RetroName=None))
    return


#==========================================================================
# Convert a name to standard by lookup
def StandardizeName(name):

    # First handle the location of the "The"
    if name[0:3] == "The ":
        name=name[4:]+", The"

    lname=name.lower()

    # First see if it is in the list of standard names
    for nt in fanacNameTuples:
        if nt.FanacStandardName != None and nt.FanacStandardName.lower() == lname:
            return nt.FanacStandardName

    # Now check other forms.
    for nt in fanacNameTuples:
        if nt.RetroName != None and nt.RetroName.lower() == lname:
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in fanacNameTuples:
        if nt.FanacDirName != None and nt.FanacDirName.lower() == lname:
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in fanacNameTuples:
        if nt.JoesName != None and nt.JoesName.lower() == lname:
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"

    for nt in fanacNameTuples:
        if nt.DisplayName != None and nt.DisplayName.lower() == lname:
            if nt.FanacStandardName != None:
                return nt.FanacStandardName
            else:
                return "StandardizeName("+name+") failed"
    return "StandardizeName("+name+") failed"
