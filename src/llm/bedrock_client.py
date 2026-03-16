from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


logger = logging.getLogger(__name__)

"""
Cliente para o Amazon Bedrock responsável por chamadas ao modelo de linguagem.

Principais responsabilidades:
- encapsular a configuração de região e IDs de modelo primário e fallback;
- expor uma interface simples para geração de texto a partir de prompts;
- tratar erros de acesso/permitsão/uso de modelo e, quando apropriado,
  alternar automaticamente para um modelo de fallback.
"""

# Modelo principal utilizado nas chamadas; o fallback é usado quando o primário
# falha por motivos como falta de permissão, use-case não submetido ou modelo
# indisponível.
DEFAULT_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
DEFAULT_FALLBACK_MODEL_ID = "amazon.nova-micro-v1:0"


def _is_fallback_worthy(exc: Exception) -> bool:
    """True if the error justifies trying the fallback model (access, permission, use-case, model not available)."""
    msg = str(exc).lower()
    if "use case" in msg or "use-case" in msg or "not submitted" in msg or "not enabled" in msg:
        return True
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "") or ""
        if code in (
            "ResourceNotFoundException",
            "AccessDeniedException",
            "ValidationException",
        ):
            return True
        if "ValidationException" in code or "AccessDenied" in code:
            return True
    return False


class BedrockClient:
    """
    Bedrock client using the Converse API. Uses primary model with automatic
    fallback to a secondary model on access/permission/use-case errors.
    """

    def __init__(self) -> None:
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self._primary_model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
        self._fallback_model_id = os.getenv("BEDROCK_FALLBACK_MODEL_ID", "").strip() or None
        if not self._fallback_model_id:
            self._fallback_model_id = DEFAULT_FALLBACK_MODEL_ID
        self.model_id = self._primary_model_id
        logger.info(
            "Initializing BedrockClient with model_id=%s, fallback=%s, region=%s",
            self.model_id,
            self._fallback_model_id,
            self.region,
        )
        self._client = boto3.client("bedrock-runtime", region_name=self.region)

    def _call_converse(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        messages = [
            {"role": "user", "content": [{"text": user_prompt}]},
        ]
        return self._client.converse(
            modelId=model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        )

    def generate_from_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        """
        Call Bedrock Converse API. Tries primary model; on access/permission/use-case
        errors, retries once with fallback model. Returns generated text or raises RuntimeError.
        """
        model_id_to_use = self.model_id
        logger.info(
            "Calling Bedrock Converse API (model_id=%s, region=%s)",
            model_id_to_use,
            self.region,
        )
        try:
            response = self._call_converse(
                model_id_to_use,
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except (BotoCoreError, ClientError) as exc:
            if (
                _is_fallback_worthy(exc)
                and self._fallback_model_id
                and self.model_id == self._primary_model_id
            ):
                logger.warning(
                    "Primary Bedrock model failed (%s), switching to fallback model: %s. Reason: %s",
                    type(exc).__name__,
                    self._fallback_model_id,
                    str(exc)[:200],
                )
                self.model_id = self._fallback_model_id
                try:
                    response = self._call_converse(
                        self.model_id,
                        system_prompt,
                        user_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    logger.info("Fallback Bedrock model succeeded.")
                except (BotoCoreError, ClientError) as fallback_exc:
                    logger.error(
                        "Fallback Bedrock model also failed: %s",
                        fallback_exc,
                        exc_info=True,
                    )
                    raise RuntimeError(
                        "Bedrock generation failed (primary and fallback). Please try again later."
                    ) from fallback_exc
            else:
                logger.error(
                    "Error calling Bedrock Converse API: %s", exc, exc_info=True
                )
                raise RuntimeError(
                    "Bedrock generation failed. Please try again later."
                ) from exc

        try:
            content = response["output"]["message"]["content"]
            for block in content:
                if "text" in block:
                    text = block["text"]
                    logger.info("Bedrock generation succeeded.")
                    return text
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unexpected response format from Bedrock: %s",
                json.dumps(response, default=str)[:1000],
            )
            raise RuntimeError(
                "Bedrock returned an unexpected response format."
            ) from exc

        logger.warning("Bedrock response did not contain any text content.")
        return ""


_singleton_client: BedrockClient | None = None


def get_bedrock_client() -> BedrockClient:
    """
    Return a singleton BedrockClient for reuse within the process.
    """
    global _singleton_client
    if _singleton_client is None:
        _singleton_client = BedrockClient()
    return _singleton_client

