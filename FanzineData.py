import FanacNames
import IssueSpec

# Define a class to hold the data I get for a particular fanzine by combining all the sources

class FanzineData:
    def __init__(self):
        self.title=None
        self.editor=None
        self.issuesText=None
        self.junk=None
        self.possible=None
        self.isHugoEligible=None
        self.fanacDirName=None
        self.fanacFanzineName=None
        self.url=None
        self.issues=IssueSpec.IssueSpecList()  # Initialize to an empty list

    def SetIsHugoEligible(self, val):
        self.isHugoEligible=val
        return self

    def SetFanacDirName(self, val):
        self.fanacDirName=val
        return self

    def SetFanacFanzineName(self, val):
        self.fanacFanzineName=val
        return self

    def SetURL(self, val):
        self.url=val
        return self

    def SetIssues(self, val):
        if val == None:
            val=IssueSpec.IssueSpecList()
        self.issues=val
        return self

    def SetJoesData(self, title, editors, issues, junk, possible):
        self.title=title
        self.editors=editors
        self.issuesText=issues
        self.junk=junk
        self.possible=possible
        return self

    def Str(self):
        return "FanzineData(title="+str(self.title)+"  issuesTxt="+str(self.issuesText)+"  ed="+str(self.editor)+"  junk="+str(self.junk)+"  poss="+str(self.possible)+ \
               "  isHElig="+str(self.isHugoEligible)+"  fzDirName="+str(self.fanacDirName)+"  fanacFzName="+str(self.fanacFanzineName)+"  url="+str(self.url)+ \
               "  issues="+self.issues.Str()