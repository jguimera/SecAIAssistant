from plugins.SECAIAssistantPlugin import SECAIAssistantPlugin
class GPTPlugin(SECAIAssistantPlugin):
    def __init__(self, name, description,plugintype,azureOpenAIClient):
        super().__init__(name, description,plugintype)
        self.azureOpenAIClient=azureOpenAIClient
    def selectplugin(self,prompt):
        #Always return True as Default plugin
        return True
    def runpromptonAzureAI(self,prompt,session):
        result_object=self.azureOpenAIClient.runPrompt(prompt,session)
        return result_object['result']
    def runprompt(self,prompt,session):
        return self.runpromptonAzureAI(prompt,session)
    #Shows the instructions to use this plugin
    def pluginhelp(self):
        return "If your prompt doens't match any other plugin checks it will be submited to the GPT model"