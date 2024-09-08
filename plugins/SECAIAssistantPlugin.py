from HelperFunctions import * 
class SECAIAssistantPlugin:
    def __init__(self, name, description,plugintype):
        self.name = name
        self.description = name
        self.type = plugintype
        print_plugin_debug(self.name,f" Loading Copilot Plugin: {self.name}")
    def printname(self):
        print(self.name)
    def getname(self):
        return self.name
    def runprompt(self,prompt,session):
        print(self.prompt)
    def selectplugin(self,prompt):
        return True
    def pluginhelp(self):
        return "Use 'string' in your prompt to generate and run KQL adhering to the Sentinel schema"
    def plugincapabilities(self):  
        capabilities={'plugincapabilitiy':"This capability allows for."}
        return  capabilities