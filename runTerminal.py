import os  
import argparse  
from colorama import Fore  
from dotenv import load_dotenv  
from SecAIAssistant  import SecAIAssistant  
from HelperFunctions import *
load_dotenv()

# Parse Arguments and decide which Authentication to use  
parser = argparse.ArgumentParser(description="AI Assistant argument parser")  
parser.add_argument("auth", choices=["interactive", "client_secret", "default"], help="Authentication method to use.")  
args = parser.parse_args()  
auth_type = args.auth  
secAIAssistant= SecAIAssistant(auth_type)
    
# AI Assistant Start  
def main():
    
    print_help("Terminal Instructions:")  
    print_help("Use 'bye' to exit.")  
    print_help("Use 'clear' to clear the session")  
    print_help("Use 'help' to show the help of the enabled plugins")  
    while True:  
        user_input = input(f"{Fore.GREEN}Prompt:{Fore.WHITE}")  
        if not user_input:
            print_info("Please enter a valid prompt")
        else:
            if user_input.lower() == "bye":  
                print_info("Bye Bye")  
                break  
            elif user_input.lower() == "clear":   
                secAIAssistant.clear_session()
            elif user_input.lower() == "help":   
                plugin_help_list=secAIAssistant.get_plugin_help()
                for plugin_help in plugin_help_list:
                    print_help(plugin_help)
            else:  
                # Run Prompt  
                processed_responses=secAIAssistant.run_prompt('terminal',user_input)
                for response in processed_responses:
                    print_response(str(response))  
if __name__ == "__main__":
    main()