from typing import Optional, Dict, Any
import os
from ..utils.logger import get_logger

logger = get_logger()


class LLMClient:
    """
    Client pour enrichir les anomalies avec un LLM Groq.
    Il gère automatiquement les modèles décommissionnés ou non accessibles.
    """

    # Modèle par défaut
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    FALLBACK_MODEL = "openai/gpt-oss-120b"  

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or self.DEFAULT_MODEL

        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY not found. LLM features disabled."
            )
            self.enabled = False
            return

        # Importer le SDK Groq de manière paresseuse pour éviter d'échouer
        # si le package n'est pas installé (LLM devient alors désactivé).
        try:
            from groq import Groq

            try:
                self.client = Groq(api_key=self.api_key)
                self.enabled = True
                logger.info(f"LLM Client initialized with Groq API (model={self.model})")
            except Exception as e:
                logger.error(f"Failed to initialize LLM Client: {e}")
                self.enabled = False
        except ImportError:
            logger.warning("groq package not installed; LLM features disabled.")
            self.enabled = False

    def validate_anomaly(self, anomaly_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {"llm_validation": None, "llm_analysis": None}

        prompt = self._build_validation_prompt(anomaly_dict)

        try:
            return self._call_model(prompt, self.model)
        except Exception as e:
            # Si modèle décommissionné ou non trouvé, bascule sur fallback
            if "model_decommissioned" in str(e) or "model_not_found" in str(e):
                logger.warning(
                    f"Modèle {self.model} indisponible, bascule sur {self.FALLBACK_MODEL}"
                )
                try:
                    return self._call_model(prompt, self.FALLBACK_MODEL)
                except Exception as e2:
                    logger.error(f"LLM fallback also failed: {e2}")
                    return {"llm_validation": False, "llm_error": str(e2)}
            else:
                logger.error(f"LLM validation error: {e}")
                return {"llm_validation": False, "llm_error": str(e)}

    def _call_model(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """Appelle Groq API avec le modèle spécifié"""
        message = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Tu es un expert en métriques et monitoring."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            top_p=0.9
        )
        llm_response = message.choices[0].message.content
        logger.debug(f"LLM Validation ({model_name}): {llm_response}")
        return {
            "llm_validation": True,
            "llm_analysis": llm_response,
            "llm_model": model_name
        }

    def _build_validation_prompt(self, anomaly: Dict[str, Any]) -> str:
        return f"""
Tu es un expert en détection d'anomalies de monitoring.
Valide si cette anomalie est réelle et fournis une analyse :

ANOMALIE DÉTECTÉE:
- Métrique: {anomaly.get('metric_name', 'unknown')}
- Type: {anomaly.get('anomaly_type', 'unknown')}
- Valeur observée: {anomaly.get('value', 'N/A')}
- Valeur attendue: {anomaly.get('expected_value', 'N/A')}
- Sévérité: {anomaly.get('severity', 'unknown')}
- Confiance du détecteur: {anomaly.get('confidence', 'N/A')}
- Description initiale: {anomaly.get('description', 'N/A')}

DEMANDES:
1. Cette anomalie est-elle réelle (Oui/Non) et pourquoi ?
2. Quel impact potentiel sur le service ?
3. Des actions recommend pour investigation ?
4. Peut-on filtrer des faux positifs ?

Sois précis et concis.
"""

# --- Fonction utilitaire pour obtenir l'instance globale ---

_llm_client = None

def get_llm_client() -> Optional[LLMClient]:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client if _llm_client.enabled else None
