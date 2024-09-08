from plugins.SECAIAssistantPlugin import SECAIAssistantPlugin  
from colorama import Fore  
import json  
import os  
from HelperFunctions import print_plugin_debug  
  
class SentinelKQLPlugin(SECAIAssistantPlugin):  
    """  
    Plugin to generate and run KQL queries adhering to the Sentinel schema.  
    """  
  
    def __init__(self, name, description, plugintype, azureOpenAIClient, sentinelClient, loadSchema=True):  
        """  
        Initialize the SentinelKQLPlugin.  
  
        :param name: Name of the plugin  
        :param description: Description of the plugin  
        :param plugintype: Type of the plugin  
        :param azureOpenAIClient: Azure OpenAI Client instance  
        :param sentinelClient: Sentinel Client instance  
        :param loadSchema: Boolean to determine if the schema should be loaded  
        """  
        super().__init__(name, description, plugintype)  
        self.azureOpenAIClient = azureOpenAIClient  
        self.sentinelClient = sentinelClient  
        self.loadSchema = loadSchema  
        self.schema_file = 'SentinelSchema.json'  
        self.sentinel_schema = None  
  
        if loadSchema:  
            self.sentinel_schema = self.loadSentinelSchema()  
  
    def pluginhelp(self):  
        """  
        Provide help instructions for this plugin.  
  
        :return: Help instructions string  
        """  
        return "Use 'kql' in your prompt to generate and run KQL adhering to the Sentinel schema."  
    def plugincapabilities(self):  
        """  
        Provide the plugin capabilities.  
  
        :return: plugin capabilities object  
        """  
        capabilities={'generateandrunkql':"This capability allows to generate a KQL query to retrieve logs and events from Microsoft Sentinel. This capability should be used when the user ask about retrieving new incidents or alerts. Other type of common data is Signin and Audit logs."}
        return  capabilities
  
    def selectplugin(self, prompt):  
        """  
        Determine if this plugin should handle the given prompt based on keywords.  
  
        :param prompt: Input prompt  
        :return: True if the plugin should handle the prompt, else False  
        """  
        return any(keyword in prompt for keyword in ["query", "kql", "sentinel schema"])  
  
    def generateSentinelSchema(self):  
        """  
        Retrieve and store the schema of Azure Sentinel tables.  
        """  
        query = "Usage | summarize by DataType"  
        query_results = self.sentinelClient.run_query(query, printresults=False)  
        table_schemas = {}  
  
        print_plugin_debug(self.name, f"Retrieving Sentinel Schema for Workspace tables ({len(query_results)})")  
  
        for table in query_results:  
            table_query = f"{table['DataType']} | getschema kind=csl"  
            table_query_results = self.sentinelClient.run_query(table_query, printresults=False)  
            table_schemas[table['DataType']] = table_query_results[0]['Schema']  
  
        with open(self.schema_file, 'w', encoding='utf-8') as f:  
            json.dump(table_schemas, f, ensure_ascii=False, indent=4)  
  
    def loadSentinelSchema(self):  
        """  
        Load the Sentinel schema from a JSON file, generating it if it doesn't exist.  
  
        :return: Loaded Sentinel schema  
        """  
        print_plugin_debug(self.name, "Loading Sentinel Schema for Workspace")  
        if not os.path.isfile(self.schema_file):  
            self.generateSentinelSchema()  
          
        with open(self.schema_file, 'r', encoding='utf-8') as f:  
            return json.load(f)  
  
    def generateKQLandRun(self, prompt, session):  
        """  
        Generate a KQL query from a prompt and run it.  
  
        :param prompt: Input prompt  
        :param session: Session context  
        :return: Result of the KQL query  
        """  
        extended_prompt = (  
            f"{prompt}\n"
            "- When asked to provide only the most recent entry use | summarize arg_max(TimeGenerated, *) by <ID Field>. Place this summarize command in the first line of the query right after the table name"   
            "- Your response must only contain the KQL code. No additional code must be added before or after the KQL code. "  
            "- Remember that this prompt might be part of a session with previous prompts and responses; therefore, you can use data from previous responses in the context if the prompt makes reference to previous results or data above."  
        )  
        prompt_result = self.runpromptonAzureAI(extended_prompt, session)  
  
        # Clean KQL tags from the result  
        prompt_result_clean = prompt_result.replace("```kql", "").replace("```kusto", "").replace("```", "").strip()  
        print_plugin_debug(self.name, f"Generated Query:\n {prompt_result_clean}")  
          
        return self.sentinelClient.run_query(prompt_result_clean, printresults=False)  
  
    def generateKQLandRunWithSchema(self, prompt, session):  
        """  
        Generate a KQL query using the schema and run it.  
  
        :param prompt: Input prompt  
        :param session: Session context  
        :return: Result of the KQL query  
        """  
        table = self.findTable(prompt, session)  
        return self.generateKQLandRunWithSchemaAndTable(prompt, table, session)  
  
    def generateKQLandRunWithSchemaAndTable(self, prompt, table, session):  
        """  
        Generate a KQL query using the schema for a specific table and run it.  
  
        :param prompt: Input prompt  
        :param table: Table name  
        :param session: Session context  
        :return: Result of the KQL query  
        """  
        try:  
            extended_prompt = (  
                f"{prompt}"
                "Always Follow this instructions to genrete the KQL query:"
                f"-Make sure you adhere to the following Schema for Table {table}: "  
                f"{self.sentinel_schema[table]}"
            )  
        except KeyError:  
            print_plugin_debug(self.name, f"Table '{table}' not found in schema. Generating Query without schema")  
            extended_prompt = prompt  
          
        return self.generateKQLandRun(extended_prompt, session)  
  
    def findTable(self, prompt, session):  
        """  
        Identify the best table to use for a given prompt.  
  
        :param prompt: Input prompt  
        :param session: Session context  
        :return: Best table name  
        """  
        table_list = ', '.join(self.sentinel_schema.keys())  
        extended_prompt = (  
            f"This is the list of available tables in my Sentinel instance: {table_list}\n"  
            "I need you to give the best available table to fulfill the prompt below:\n"  
            f"Prompt (Do not run): {prompt}\n"  
            "Make sure you ONLY respond with the name of the table avoiding any other text or character."  
        )  
        table = self.runpromptonAzureAI(extended_prompt, session)  
        print_plugin_debug(self.name, f"Selected Table: {table}")  
        return table  
  
    def runpromptonAzureAI(self, prompt, session):  
        """  
        Run a given prompt on the Azure OpenAI client.  
  
        :param prompt: Input prompt  
        :param session: Session context  
        :return: Response from Azure OpenAI Client  
        """  
        return self.azureOpenAIClient.runPrompt(prompt, session)['result'] 
  
    def runprompt(self, prompt, session):  
        """  
        Convenience method to run the prompt and generate a KQL query with or without schema based on the plugin configuration.  
        :param prompt: Input prompt  
        :param session: Session context  
        :return: Result of the KQL query  
        """ 
        result=''
        if self.loadSchema: 
            result= self.generateKQLandRunWithSchema(prompt, session) 
        else: 
            result= self.generateKQLandRun(prompt, session)
        return result
