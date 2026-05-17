"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_system_text(data: dict) -> str:
    """Extrai o conteúdo do system prompt."""
    for msg in data.get("messages", []):
        if "system" in msg:
            return msg["system"] or ""
    return ""


def get_full_text(data: dict) -> str:
    """Extrai todo o texto do prompt (system + human)."""
    parts = []
    for msg in data.get("messages", []):
        for value in msg.values():
            if value:
                parts.append(value)
    return "\n".join(parts)


@pytest.fixture(scope="module")
def prompt_data():
    return load_prompts(PROMPT_FILE)


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        system_text = get_system_text(prompt_data)
        assert system_text.strip(), "O system prompt está ausente ou vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        system_text = get_system_text(prompt_data)
        assert "Você é" in system_text, (
            "O system prompt não define uma persona. "
            "Use 'Você é um [papel]' para definir o papel do assistente."
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_text = get_system_text(prompt_data)
        format_indicators = [
            "Como um",           # formato User Story
            "Critérios de Aceitação",  # seção padrão de US
            "Given",             # Given-When-Then
            "Dado que",          # Given-When-Then em PT
            "Quando",
            "Então",
            "Markdown",
            "##",                # cabeçalho Markdown
        ]
        found = [kw for kw in format_indicators if kw in system_text]
        assert found, (
            "O prompt não especifica o formato de saída esperado. "
            f"Nenhum dos indicadores encontrados: {format_indicators}"
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_text = get_system_text(prompt_data)
        has_bug_example = "BUG REPORT:" in system_text or "bug_report" in system_text.lower()
        has_story_example = "USER STORY:" in system_text or "Como um" in system_text
        assert has_bug_example and has_story_example, (
            "O prompt não contém exemplos de few-shot. "
            "Inclua pelo menos um par BUG REPORT / USER STORY no system prompt."
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum [TODO] no texto."""
        full_text = get_full_text(prompt_data)
        todo_markers = ["[TODO]", "TODO", "FIXME", "XXX"]
        found = [marker for marker in todo_markers if marker in full_text]
        assert not found, (
            f"O prompt contém marcadores inacabados: {found}. "
            "Remova ou substitua antes de publicar."
        )

    def test_minimum_techniques(self, prompt_data):
        """Verifica se pelo menos 2 técnicas de prompt engineering estão aplicadas."""
        system_text = get_system_text(prompt_data)
        full_text = get_full_text(prompt_data)

        techniques_found = []

        if "Você é" in system_text:
            techniques_found.append("Role Assignment")

        few_shot_markers = ["BUG REPORT:", "USER STORY:", "---"]
        if sum(1 for m in few_shot_markers if m in system_text) >= 2:
            techniques_found.append("Few-Shot Prompting")

        if any(kw in system_text for kw in ["SEMPRE", "NUNCA", "obrigatório", "REGRAS"]):
            techniques_found.append("Explicit Rules")

        if any(kw in system_text for kw in ["edge case", "Edge Case", "Se o bug", "Se o relato"]):
            techniques_found.append("Edge Case Handling")

        if any(kw in full_text for kw in ["raciocine", "pense", "antes de escrever", "raciocínio"]):
            techniques_found.append("Chain-of-Thought")

        if any(kw in system_text for kw in ["Como um", "Dado que", "Quando", "Então", "Given", "When", "Then"]):
            techniques_found.append("Explicit Output Format")

        assert len(techniques_found) >= 2, (
            f"Apenas {len(techniques_found)} técnica(s) detectada(s): {techniques_found}. "
            "O mínimo exigido são 2 técnicas de prompt engineering."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
