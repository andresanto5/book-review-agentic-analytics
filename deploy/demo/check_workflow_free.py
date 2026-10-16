"""Real HTTP routing/MCP/database; deterministic generation double, no AWS."""
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

class SimulatedGenerator:
    model_id = "SIMULATED-NO-AWS"
    calls = 0
    def generate_from_messages(self, *, system_prompt, user_prompt, **kwargs):
        assert "DEMO-SYNTHETIC:" in user_prompt, "Expected real fixture rows in prompt"
        assert system_prompt and user_prompt
        self.calls += 1
        return "[SIMULAÇÃO LOCAL — SEM LLM/AWS] O contexto das ferramentas foi recebido. Esta resposta fixa testa a integração e não avalia a qualidade de geração de texto."

generator = SimulatedGenerator()
cases = [
    ("Which books are most reviewed?", "structured", True, False),
    ("Summarize Python programming reviews", "semantic", False, True),
    ("Which books are most reviewed and why?", "hybrid", True, True),
]
report = {"generation":"deterministic test double, not an LLM", "aws_calls":0, "cases":[]}
with patch("src.llm.bedrock_client.boto3.client", side_effect=AssertionError("AWS blocked")), patch("src.agents.langgraph_nodes.get_bedrock_client", return_value=generator):
    client = TestClient(app)
    for question, strategy, structured, semantic in cases:
        response = client.post("/chat/ask", json={"question":question})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["strategy"] == strategy, result
        assert not result["errors"], result
        assert result["final_answer"].startswith("[SIMULAÇÃO LOCAL"), result
        assert result["model_id"] == "SIMULATED-NO-AWS", result
        assert bool(result["structured_rows"]) == structured, result
        assert bool(result["semantic_rows"]) == semantic, result
        report["cases"].append({"strategy":strategy,"structured_rows":result["structured_rows"],"semantic_rows":result["semantic_rows"],"time_ms":result["total_time_ms"],"generation":"SIMULATED-NO-AWS","status":"passed"})
    previous_calls = generator.calls
    for question in ("Which book sold the most?", "Qual a categoria com o autor que tem melhores avaliações?"):
        response = client.post("/chat/ask", json={"question":question})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["strategy"] in ("out_of_scope","unsupported_composite"), result
        assert generator.calls == previous_calls
        report["cases"].append({"strategy":result["strategy"],"generation":"skipped","status":"passed"})
assert generator.calls == 3
print(json.dumps(report, ensure_ascii=False))
