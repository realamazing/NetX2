


class Relationship:
    def __init__(self,name,sources,destinations) -> None:
        self.name = name
        self.sources = sources
        self.destinations = destinations
    def connect(self):
        print(self.sources,self.destinations)
    def printname(self):
        print(self.name)

class Action(Relationship):
    def __init__(self,name,sources,destinations) -> None:
        super().__init__(name,sources,destinations)

class Clause(Relationship):
    def __init__(self,name,sources,destinations) -> None:
        super().__init__(name,sources,destinations)

R = Relationship('test',[],[])
R.connect()

E = Action('im an action relationship',[],[])
E.connect()
print(type(E))

C = Clause('im a clause relationship',[],[])
C.printname()