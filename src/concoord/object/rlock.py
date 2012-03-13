"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example rlock object
@copyright: See LICENSE
"""
from concoord.threadingobject.drlock import DRLock

class RLock():
    """RLock object that supports following functions:
    - acquire: locks the object recursively
    - release: unlocks the object
    """
    def __init__(self, **kwargs):
        self.rlock = DRLock()

    def __repr__(self, **kwargs):
        return repr(self.rlock)

    def acquire(self, **kwargs):
        try:
            return self.rlock.acquire(kwargs)
        except Exception as e:
            raise e
        
    def release(self, **kwargs):
        try:
            self.rlock.release(kwargs)
        except Exception as e:
            raise e
    
    def __str__(self, **kwargs):
        return str(self.rlock)