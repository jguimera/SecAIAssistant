from openai import AzureOpenAI,BadRequestError,APIConnectionError
from colorama import Fore
class AzureOpenAIClient():
    def __init__(self,api_key,azure_endpoint,model_name):
        self.model_name=model_name
        self.client=AzureOpenAI(
        azure_endpoint = azure_endpoint, 
        api_key=api_key,  
        api_version="2024-02-15-preview"
        )
    
    def runPrompt(self,prompt,session=[]):
        message_object = [{"role":"system","content":"As an AI specializing in security analytics, your task is to analyze and write Sentinel Analytic rules based on KQL queries and other properties. You are also an expert in summarizing Security data and events."}]
        message_object.extend(session)
        message_object.append({"role":"user","content":prompt})
        result=''
        status='success'
        session_tokens=''
        try:
            completion = self.client.chat.completions.create(
            model=self.model_name,#Deployment Name
            messages = message_object,
            temperature=0.7,
            max_tokens=4000,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
            )
            result=completion.choices[0].message.content
            session_tokens=str(completion.usage.total_tokens)
        except BadRequestError as e:  
            status='error'
            result=e.code+' - '+e.message
        except APIConnectionError as e:
            status='error'
            result=e.code+' - '+e.message
        result_object={"status":status,"result":result,"session_tokens":session_tokens}
        return result_object