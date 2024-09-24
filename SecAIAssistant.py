import os  
from azure.identity import InteractiveBrowserCredential, ClientSecretCredential, DefaultAzureCredential  
from clients.SentinelClient import SentinelClient  
from clients.AzureOpenAIClient import AzureOpenAIClient  
from plugins.SentinelKQLPlugin import SentinelKQLPlugin  
from plugins.GPTPlugin import GPTPlugin  
from plugins.FetchURLPlugin import FetchURLPlugin  
from colorama import Fore  
from HelperFunctions import *  
import json 
class SecAIAssistant:  
    def __init__(self, auth_type):  
        self.client_list = {}  
        self.plugin_list = {} 
        self.plugin_capabilities={}
        self.session = []  
        self.context_window_size = int(os.getenv('ASSISTANT_CONTEXT_WINDOW_SIZE', 5))  
        self.print_intro_message()  
        self.auth(auth_type)  
        self.create_clients()  
        self.load_plugins()  
        self.load_plugin_capabilities()
  
    def auth(self, auth_type):  
        """  
        Authenticate with Azure using different credential types based on the provided auth_type.  
        """  
        # Use different types of Azure Credentials based on the argument  
        if auth_type == "interactive":  
            self.credential = InteractiveBrowserCredential()  
        elif auth_type == "client_secret":  
            self.credential = ClientSecretCredential(  
                tenant_id=os.getenv('AZURE_TENANT_ID'),  
                client_id=os.getenv('AZURE_CLIENT_ID'),  
                client_secret=os.getenv('AZURE_CLIENT_SECRET')  
            )  
        else:  
            # Managed Identity to be used when running in Azure Serverless functions.  
            self.credential = DefaultAzureCredential()  
  
        # Force authentication to make the user login  
        print_info("Authenticating with Azure...")  
        try:  
            self.credential.get_token("https://management.azure.com/.default")  
            print_info("Authentication successful")  
        except Exception as e:  
            print_error(f"Authentication failed: {e}")  
            print_error("Only unauthenticated plugins can be used")  
  
    def create_clients(self):  
        """  
        Create clients to external platforms using environment variables.  
        """  
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')  
        resource_group_name = os.getenv('AZURE_RESOURCEGROUP_NAME')  
        workspace_name = os.getenv('AZURE_WORKSPACE_NAME')  
        workspace_id = os.getenv('AZURE_WORKSPACE_ID')  
          
        self.client_list["sentinel_client"] = SentinelClient(  
            self.credential, subscription_id, resource_group_name, workspace_name, workspace_id  
        )  
  
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')  
        api_key = os.getenv('AZURE_OPENAI_APIKEY')  
        model_name = os.getenv('AZURE_OPENAI_MODELNAME')  
          
        self.client_list["azure_openai_client"] = AzureOpenAIClient(api_key, azure_endpoint, model_name)  
  
    def load_plugins(self):  
        """  
        Load plugins for the assistant. Currently hardcoded, but can be extended to auto-load from the plugins folder.  
        """  
        # TODO: Auto-load from all plugins available inside the plugins subfolder  
        self.plugin_list = {  
            "SentinelKQLPlugin": SentinelKQLPlugin(  
                "SentinelKQLPlugin", "Plugin to generate and run KQL queries in Sentinel", "API",   
                self.client_list["azure_openai_client"], self.client_list["sentinel_client"],loadSchema=True  
            ),  
            "FetchURLPlugin": FetchURLPlugin(  
                "FetchURLPlugin", "Plugin to fetch HTML sites", "API",   
                self.client_list["azure_openai_client"]  
            ),  
            "GPTPlugin": GPTPlugin(  
                "GPTPlugin", "Plugin to run prompts in Azure OpenAI GPT models", "GPT",   
                self.client_list["azure_openai_client"]  
            )  
        }  
    def load_plugin_capabilities(self):
        self.plugin_capabilities={}
        for plugin_name in self.plugin_list.keys():
            plugincapability=self.plugin_list[plugin_name].plugincapabilities()
            self.plugin_capabilities[plugin_name]= plugincapability
    def select_plugin(self, prompt):  
        """  
        Select the appropriate plugin based on the input prompt. Each prompt decides based on internal checks.  
        TODO: Use AI model to decide the plugin.  
        """  
        new_prompt = prompt.lower()  
        for plugin_name in self.plugin_list.keys():  
            plugin = self.plugin_list[plugin_name]  
            selected = plugin.selectplugin(new_prompt)  
            if selected:  
                selected_plugin_name = plugin.getname()  
                print_info(f"Selected plugin: {selected_plugin_name}")  
                return selected_plugin_name  
    def decompose_in_tasks(self, prompt):  
        """  
        Select the appropriate plugin based on the input prompt. Each prompt decides based on internal checks.  
        """  
        system_message = (  
                'You are an AI assistant that is part of a system that takes a user prompt and process it with one or more of the capabilities from the available plugins.\n '
                'You will receive the user prompt and the list of available plugins and its capabilities in JSON format.\n'  
                'Each plugin might have one or more capabilities.\n'
                'Your task is to select the most appropiate plugins and capabilities to process the user prompt.\n'  
                'Evaluate if the prompt of the user can be answered by only one of the capabilities or you need to decompose the prompt in multiple sub-prompts(tasks) that will be executed sequentially.'
                'When decompasing the user prompt in multiple sub-prompts take into account that each sub-prompt will have the results of the precious ones as context.'
                'In case only one prompt is needed, make sure you still return an array with just one element and reformat the user prompt to achieve better results.'
                'I will parse the output inside a python script so It must be returned using only JSON format and will follow this schema [{"plugin_name":"<selecte_plugin_name>","capability_name":"<selected_capability_name>","prompt":"new sub-prompt"}]\n'  
                )
        sample_user_prompt='Can you please list the last Sentinel Incidents with High Severity'
        example_user_message=(
            'Please I need you to return the best available plugin and capabilitiy to fulfill the user prompt. Follow the previous instructions.\n'
            'This is the list of available plugins and its capabilities:'
            f'{self.plugin_capabilities}'
            'This is the user prompt:'
            f'{sample_user_prompt}'
            )
        example_assistant_message=(
                '[{"plugin_name":"SentinelKQLPlugin","capability_name":"generateandrunkql"}]'  
            )
        system_object = {"role":"system","content":system_message}
        user_object = {"role": "user", "content": [{"type": "text", "text": example_user_message}]}  
        assistant_object = {"role": "assistant", "content": [{"type": "text", "text": example_assistant_message}]}  
        new_session=[]
        new_session.append(system_object)  
        new_session.append(user_object)  
        new_session.append(assistant_object)
        #print(new_session)
        selected_plugin_string= self.plugin_list["GPTPlugin"].runprompt(prompt, new_session)  
        # Clean tags from result  
        selected_plugin_string_clean = selected_plugin_string.replace("```plaintext", "").replace("```json", "").replace("```", "")  
        print(selected_plugin_string_clean)
        obj = json.loads(selected_plugin_string_clean) 
        return obj
    def get_plugin(self, plugin_id):  
        """  
        Get the plugin instance by its ID.  
        """  
        return self.plugin_list[plugin_id]  
    def get_plugin_help(self):  
        """  
        Get the plugin help information.  
        """
        plugin_help_list=[]  
        for plugin_name in self.plugin_list.keys():  
            plugin = self.plugin_list[plugin_name]  
            plugin_help = plugin.pluginhelp()
            plugin_help_list.append(plugin_help) 
        return plugin_help_list 
    def print_intro_message(self):  
        """  
        Print the introductory message for the assistant.  
        """  
        message = """
   _____ ______ _____            _____                    _     _              _   
  / ____|  ____/ ____|     /\   |_   _|     /\           (_)   | |            | |  
 | (___ | |__ | |         /  \    | |      /  \   ___ ___ _ ___| |_ __ _ _ __ | |_ 
  \___ \|  __|| |        / /\ \   | |     / /\ \ / __/ __| / __| __/ _` | '_ \| __|
  ____) | |___| |____   / ____ \ _| |_   / ____ \\__ \__ \ \__ \ || (_| | | | | |_ 
 |_____/|______\_____| /_/    \_\_____| /_/    \_\___/___/_|___/\__\__,_|_| |_|\__|
                                                                                   
            """ 
        print(f"{Fore.GREEN}{message}{Fore.WHITE}")  
        print_info("Welcome to SEC AI Assistant")  
  
    def process_response(self, output_type, user_input, response):  
        """  
        Process the response to format it for specific output types (Terminal, HTML, etc.).  
        """  
        if output_type == 'terminal':  
            extended_prompt = (  
                'Below you have a prompt and the response associated with it. '  
                'Based on the prompt I need you to format the provided response to be shown in a terminal console. '  
                'If the response is a JSON object format it in a table for the terminal output unless specified otherwise below. '  
                'Make sure that the output table fits the screen. If a field takes more than 40 characters you should truncate it.\n'
                'Make sure you remove any reference to BlueVoyant or BV from the results. You can replace it with the text SEN.\n'   
                f'This is the original prompt (only use it to format the output): {user_input}\n'  
                f'This is the original prompt response (this is the data you have to format): \n{response}'  
            )  
        elif output_type == 'html':  
            extended_prompt = (  
                'Below you have a prompt and the response associated with it. '  
                'Based on the prompt I need you to format the provided response to be shown in a browser in HTML format. '  
                'If the response is a JSON object format it in a table for the HTML output. '  
                'Make sure that the output html table is responsive. If a field takes more than 40 characters you can truncate it.\n'  
                f'This is the original prompt (only use it to format the output): {user_input}\n'  
                f'This is the original prompt response (this is the data you have to format): \n{response}'  
            )  
        elif output_type == 'other':  
            extended_prompt = (  
                'Below you have a prompt and the response associated with it. '  
                'Based on the prompt I need you to format the provided response to be shown using plain text format. '  
                'If the response is a JSON object format it in a table for the plain text output. '  
                'Make sure that the output html table is responsive. If a field takes more than 40 characters you can truncate it.\n'  
                f'This is the original prompt (only use it to format the output): {user_input}\n'  
                f'This is the original prompt response (this is the data you have to format): \n{response}'  
            )  
  
        prompt_result = self.plugin_list["GPTPlugin"].runprompt(extended_prompt, [])  
        # Clean tags from result  
        prompt_result_clean = prompt_result.replace("```plaintext", "").replace("```kusto", "").replace("```", "")  
        return prompt_result_clean  
  
    def run_prompt(self, output_type, prompt):  
        """  
        Run the provided prompt using the selected plugin and process the response.  
        """  
        task_results=[]
        decomposed_tasks=self.decompose_in_tasks(prompt)
        for task in decomposed_tasks:
            plugin_response = self.get_plugin(task['plugin_name']).runprompt(task['prompt'], self.session)  
            self.update_session(prompt, plugin_response)  
            processed_response = self.process_response(output_type, prompt, str(plugin_response))
            task_results.append(processed_response)  
        print_info(f"Processing Response (Session Lenght: {len(self.session)})")  
        return task_results  
  
    def update_session(self, prompt, plugin_response):  
        """  
        Update the session with the latest prompt and response.  
        """  
        user_object = {"role": "user", "content": [{"type": "text", "text": prompt}]}  
        assistant_object = {"role": "assistant", "content": [{"type": "text", "text": str(plugin_response)}]}  
  
        if len(self.session) >= self.context_window_size * 2:  
            self.session.pop(0)  # Remove the oldest element twice (Assistant and User)  
            self.session.pop(0)  
  
        self.session.append(user_object)  
        self.session.append(assistant_object)  
  
    def clear_session(self):  
        """  
        Clear the current session.  
        """  
        print_info("Session Cleared")  
        self.session.clear()  
