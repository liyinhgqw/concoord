'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Test proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Test:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, debug=True)
        
    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def getvalue(self):
        return self.proxy.invoke_command('getvalue')

    def setvalue(self, newvalue):
        return self.proxy.invoke_command('setvalue', newvalue)

    def __str__(self):
        return self.proxy.invoke_command('__str__')
