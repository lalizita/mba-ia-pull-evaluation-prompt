"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)
"""

import os
import sys
import yaml
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import check_env_vars, print_section_header

load_dotenv()

PROMPT_METADATA = {
    "bug_to_user_story_v2": {
        "file": "prompts/bug_to_user_story_v2.yml",
        "description": (
            "Prompt otimizado para converter relatos de bugs em User Stories ágeis. "
            "Técnicas: Role Assignment, Few-Shot Prompting, Explicit Output Format, "
            "Explicit Rules, Edge Case Handling, System/User Separation, "
            "Positive Framing, Chain-of-Thought via Scratchpad Implícito."
        ),
        "tags": [
            "bug-analysis",
            "user-story",
            "product-management",
            "few-shot",
            "chain-of-thought",
            "agile",
            "given-when-then",
            "optimized",
            "ChatPromptTemplate",
        ],
    }
}


def load_prompt_file(file_path: str) -> dict | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Erro ao parsear YAML: {e}")
        return None


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []

    if not prompt_data:
        return False, ["Arquivo YAML vazio ou inválido"]

    messages = prompt_data.get("messages", [])
    if not messages:
        errors.append("Nenhuma mensagem encontrada no prompt")

    roles = [list(m.keys())[0] for m in messages if m]
    if "system" not in roles:
        errors.append("system prompt ausente")
    if "human" not in roles:
        errors.append("human prompt ausente")

    full_text = " ".join(str(v) for m in messages for v in m.values())
    if "{bug_report}" not in full_text:
        errors.append("Variável {bug_report} não encontrada")

    system_text = next((m["system"] for m in messages if "system" in m), "")
    if len(system_text.strip()) < 100:
        errors.append("system prompt muito curto — verifique o conteúdo")

    return (len(errors) == 0, errors)


def build_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    messages = []
    for msg in prompt_data.get("messages", []):
        if "system" in msg:
            messages.append(("system", msg["system"]))
        elif "human" in msg:
            messages.append(("human", msg["human"]))
    return ChatPromptTemplate.from_messages(messages)


def push_commit(
    prompt_name: str,
    template: ChatPromptTemplate,
    metadata: dict,
) -> bool:
    client = Client()
    username = client._get_settings().tenant_handle
    full_name = f"{username}/{prompt_name}"

    try:
        url = client.push_prompt(
            full_name,
            object=template,
            is_public=True,
            description=metadata["description"],
            tags=metadata["tags"],
        )
        print(f"   ✓ Prompt publicado publicamente!")
    except Exception as e:
        if "Nothing to commit" in str(e):
            print("   ℹ️  Sem mudanças desde o último commit — prompt já está atualizado.")
            url = f"https://smith.langchain.com/hub/{full_name}"
        else:
            raise

    print(f"   URL: {url}")
    return True


def main():
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    print(f"Prompts a publicar: {list(PROMPT_METADATA.keys())}\n")

    all_succeeded = True

    for prompt_name, metadata in PROMPT_METADATA.items():
        print_section_header(f"Prompt: {prompt_name}", char="-", width=40)

        print(f"Carregando {metadata['file']}...")
        prompt_data = load_prompt_file(metadata["file"])
        if prompt_data is None:
            all_succeeded = False
            continue

        print(f"Validando '{prompt_name}'...")
        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            print("❌ Validação falhou:")
            for err in errors:
                print(f"   - {err}")
            all_succeeded = False
            continue
        print("   ✓ Validação passou")

        template = build_prompt_template(prompt_data)

        try:
            success = push_commit(prompt_name, template, metadata)
        except Exception as e:
            print(f"❌ Erro ao fazer push: {e}")
            success = False

        if not success:
            all_succeeded = False

    print()
    if all_succeeded:
        print("✅ Todos os prompts foram publicados com sucesso!")
        print("\nVerifique em: https://smith.langchain.com/prompts")
        return 0
    else:
        print("❌ Um ou mais prompts falharam no push.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
