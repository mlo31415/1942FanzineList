import collections
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
            print("*** Read1942FanzineList: Could not find opening '(' in '"+line+"'")
            continue

        loc2=line.find(")", loc1)
        if loc2==-1:
            print("*** Read1942FanzineList: Could not find closing ')' in '"+line+"'")
            continue

        allFanzines1942.append(JoesData(line[:loc1-1], line[loc1+1:loc2].title(), line[loc2+1:]))
        FanacNames.AddJoesName(line[:loc1-1])


    f.close()
    print("----fanzines1942 list created with "+str(len(allFanzines1942))+" elements")
    print("----Done reading Joe's 1942 Fanzine List.txt")
    return allFanzines1942
