import FanzineData
import FanacNames
import re

# ============================================================================================
# Read the 1942 All Fanzine list and extract all the names and add them to the fanacNameTuples list
# All we want to do here is extract the fanzines names and add them to the list of named tuples.
def Read1942FanzineList():
    print("----Begin reading Joe's 1942 Fanzine List.txt")

    # OK, next we open the complete list of 1942 fanzines from Joe Siclari.
    # Each line follows a vague pattern:
    # <title> '(' <name of editor(s) ')' <a usually comma-separated list of issues> <crap, frequently in parenthesis>
    # Store the parsed information in a list of tuples
    f=open("1942 All Fanzines List.txt")
    allFanzines1942=[]
    for line in f:  # Each line is a fanzine
        if line[-1:]=="\n":  # Drop the trailing newline
            line=line[:-1]
        print("\n"+line)
        temp="".join(line.split())  # This is a Python idiom which removes whitespace from a string
        if len(temp)==0:  # Ignore lines that are all whitespace
            continue

        # OK, like everything in this document else, this is...untidy...data
        # There are up to four sections which appear in a somewhat random order
        # The name is always first
        # The other three sections are:
        #   The issue list (One or more issue designations).  Nearly always present
        #   The editor list. (One or more names in parenthesis.  Nearly always present
        #   Misc. crap. (Basically a gnomic string usually in parenthesis and usually at the end.)  Sometimes present.

        # Locate up to two parenthesized chunks, save them, and replace them by a single "|" character (since they act as delimiters.)
        editors=""
        junk=""
        loc1=line.find("(")
        if loc1 != -1:
            loc2=line.find(")", loc1)
            if loc2 != -1:
                editors=line[loc1+1:loc2].strip()
                line=line.replace("("+editors+")", "|") # Turn the editors into a "|"

                # See if there's a second parenthesized chunk
                loc1=line.find("(")
                if loc1 != -1:
                    loc2=line.find(")", loc1)
                    if loc2 != -1:
                        junk=line[loc1+1:loc2].strip()
                        line=line.replace("("+junk+")", "|") # Turn the junk into a "|"

        # OK, now see if we can find the title
        # We know it starts at the beginning.  It always ends at "|".  But sometimes it is followed by the issue list.
        # Start by finding the string fromt he start of the line to the first delimiter ("|" or eol).  This will contain the name and *may* contain the issue list.
        loc1=line.find("|")
        if loc1 != -1:
            startstuff=line[:loc1-1].strip()
            line=line[loc1:].strip()
        else:
            startstuff=line.strip()
            line=""

        # If there's non-whitespace material between two "|"s or between one "|" and eol, this is the issue list
        possible=""
        loc1=line.find("|")
        if loc1 > -1:
            loc2=line.find("|", loc1+1)
            if loc2 > -1:
                # Two "|"s.
                possible=line[loc1+1:loc2].strip()
                line=line[:loc1-1]+line[:loc2].strip()
            else:
                possible=line[loc1+1:].strip()
                line=""

        # If 'possible' contains any digits, it's nearly certainly the issue list, and startStuff is the title
        issues=""
        title=""
        found=False
        if len(possible) > 0:
            hasDigit=not all([not x.isdigit() for x in possible])   # Isn't this cute? Comprehension creates list of logical from test of isdigit() on each character, and all does an and of them all
            if hasDigit:
                title=startstuff
                issues=possible
                possible=""
                found=True
        if not found:
            # We need to split startStuff
            # The basic problem is that neither the structure of the name nor of the issue list is well-defined.
            # We can count on them being separated by whitespace, and we can count on the issue list starting with either a numeral or a "V" followed by a numeral.  And not on much else.
            # So we will split at the first occurance of whitespace-numeral or whitespace-'V'-numeral
            p=re.compile("^(.+?)(\s*[Vv]?\d)(.*)$")
            m=p.match(startstuff)
            if m != None and len(m.groups()) == 3:
                print("   pattern match: ", m.groups())
                title=m.groups()[0]
                issues=m.groups()[1]+m.groups()[2]
            else:
                title=startstuff
                issues=""

        print("   startStuff='"+str(startstuff)+"'   title='"+str(title)+"'   editors='"+str(editors)+"'    issuesText='"+str(issues)+"'   junk='"+str(junk)+"'   possible='"+str(possible)+"'   line='"+str(line)+"'")

        fd=FanzineData.FanzineData()
        fd.SetJoesData(title, editors, issues, junk, possible)
        allFanzines1942.append(fd)
        FanacNames.AddJoesName(line[:loc1-1])


    f.close()
    print("----fanzines1942 list created with "+str(len(allFanzines1942))+" elements")
    print("----Done reading Joe's 1942 Fanzine List.txt")
    return allFanzines1942
