import json
from pathlib import Path


def test_handoff_request_schema_contract_shape() -> None:
    schema_path = Path(".agentic/transfer/schemas/handoff_request.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "agentic-project-kit local-to-LLM handoff request"
    required = set(schema["required"])
    for key in {
        "schema_version",
        "kind",
        "message_kind",
        "assignment_kind",
        "repo",
        "llm_assignment",
        "transfer_protocol_machine",
        "required_sources",
        "command_inventory",
        "blockers",
    }:
        assert key in required
    assert schema["properties"]["kind"]["const"] == "local_to_llm_last_result"
    assert schema["properties"]["message_kind"]["const"] == "handoff_request"
    assert schema["properties"]["assignment_kind"]["const"] == "successor_chat_prompt"


def test_successor_handoff_prompt_template_contract() -> None:
    template_path = Path(".agentic/transfer/templates/successor_handoff_prompt.md")
    text = template_path.read_text(encoding="utf-8")
    assert text.startswith("Wir arbeiten im Repo `{repo_full_name}`.")
    assert "{local_path_command}" in text
    assert "{prompt_state_json}" in text
    assert "{required_sources}" in text
    assert "{transfer_rules}" in text
    assert "Ich erstelle" not in text
    assert "Hier ist" not in text
