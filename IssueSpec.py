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

    def Str(self):
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

    def Str(self):
        s=""
        for i in self.list:
            if len(s) > 0:
                s=s+", "
            if i != None:
                s=s+i.Str()
            else:
                s=s+"Missing ISlist"
        if len(s) == 0:
            s="Empty ISlist"
        return s

    def len(self):
        return len(self.list)

    def List(self):
        return self.list