#------------------------------------------------------------------------
# This is a class which will always return the External Links table.
# It will read it the first time it is initialized and thereafter just return it.
# Usage: x=ExternalClass().List()
global g_externalLinks1942
g_externalLinks1942=[]

class ExternalLinks:
    def __init__(self):
        import collections
        global g_externalLinks1942
        if len(g_externalLinks1942) == 0:
            print("----Begin reading External Links 1942.txt")
            # Now we read Links1942.txt, which contains links to issues of fanzines *outside* fanac.org.
            # It's organized as a table, with the first row a ';'-delimited list of column headers
            #    and the remaining rows are each a ';'-delimited pointer to an exteral fanzine
            # First read the header line which names the columns.  The headers are separated from ';", so we need to remove these.
            f=open("External Links 1942.txt")
            line=f.readline()
            line=line.replace(";", "")
            links1942ColNames=line.split(" ")
            # Define a named tuple to hold the data I get from the external links input file
            # This -- elegantly -- defines a named tuple to hold the elements of a line and names each element according to the column header in the first row.
            ExternalLinksData=collections.namedtuple("ExternalLinksData", line)

            # Now read the rest of the data.
            for line in f:  # Each line after the first is a link to an external fanzine
                print("   line="+line.strip())
                temp=line.split(";")
                t2=[]
                for t in temp:
                    t2.append(t.strip())
                g_externalLinks1942.append(ExternalLinksData(*tuple(t2)))  # Turn the list into a named tuple.
            f.close()
            print("----Done reading External Links 1942.txt")

    def List(self):
        return g_externalLinks1942