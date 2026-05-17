"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain import hub
from utils import save_yaml, print_section_header

load_dotenv()


def prompt_to_dict(prompt) -> dict:
    messages = []
    for msg in prompt.messages:
        role = msg.__class__.__name__.replace("MessagePromptTemplate", "").lower()
        template = msg.prompt.template
        messages.append({role: template})
    return {
        "input_variables": prompt.input_variables,
        "messages": messages,
    }


def pull_prompts_from_langsmith():
    print("Pulling prompts from LangSmith...")
    client = Client(api_key=None)
    prompt = client.pull_prompt("leonanluppi/bug_to_user_story_v1")
    data = prompt_to_dict(prompt)
    save_yaml(data, "prompts/bug_to_user_story_v1.yml")
    print("Prompts saved successfully")


def main():
    """Função principal"""
    pull_prompts_from_langsmith()


if __name__ == "__main__":
    sys.exit(main())
