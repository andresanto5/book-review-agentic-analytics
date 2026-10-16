"""Checks real application routes without allowing Bedrock requests."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

# Do not run startup: model download is independently checked during stack startup.
# Any unintended model invocation fails the test instead of contacting AWS.
with patch("src.llm.bedrock_client.boto3.client", side_effect=AssertionError("AWS disabled in local checks")):
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    for question in ("Qual livro mais vendeu?", "Quais livros venderam mais?", "Qual o livro mais vendido?", "Which book sold the most?"):
        response = client.post("/chat/ask", json={"question": question})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["out_of_scope"] is True, body
        assert body["final_answer"], body
    assert client.post("/chat/ask", json={}).status_code == 422
print("PASS: HTTP health, out-of-scope guardrail, required question; AWS calls blocked")
