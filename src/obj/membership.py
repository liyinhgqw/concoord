class Membership():
    """Object to keep track of members in a system.
    Supports functions:
    - add: adds a member
    - remove: removes a member
    """
    def __init__(self):
        self.members = set()

    def add(self, args, **kwargs):
        member = args[0]
        if member not in self.members:
            self.members.add(member)
        
    def remove(self, args, **kwargs):
        member = args[0]
        if member in self.members:
            self.members.remove(member)
        else:
            raise KeyError(member)
        
    def __str__(self):
        return " ".join([str(m) for m in self.members])