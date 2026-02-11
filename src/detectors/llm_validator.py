"""
Validateur LLM pour les anomalies détectées.

This detector uses a free LLM (Groq API with Llama 2/Mixtral) to:
- Validate if anomalies are real or false positives
- Add intelligent context and analysis
- Generate smart recommendations

Conçu pour enrichir (pas remplacer) les détecteurs statistiques.
"""

from typing import List, Optional, Dict, Any
from .base_detector import BaseDetector
from ..models.metric import Metric
from ..models.anomaly import Anomaly, Severity
from ..utils.llm_client import get_llm_client
from ..utils.logger import get_logger

logger = get_logger()


class LLMValidator(BaseDetector):
    """
    Meta-détecteur qui utilise un LLM pour valider les anomalies existantes.
    
    Ne détecte PAS d'anomalies mais les enrichit et valide.
    Prend une liste d'anomalies et les analyse avec le LLM.
    
    Cas d'usage:
    - Filtrer les faux positifs
    - Ajouter du contexte business
    - Valider la sévérité
    - Générer des recommandations d'action
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le validateur LLM.
        
        Args:
            config: Configuration du détecteur
        """
        super().__init__(config)
        
        # Initialiser le client LLM
        self.llm_client = get_llm_client()
        
        if self.llm_client:
            logger.info("LLMValidator initialized successfully")
        else:
            logger.warning("LLMValidator: LLM client not available (API key missing)")
            self.enabled = False
    
    def detect(self, metric: Metric) -> List[Anomaly]:
        """
        Cette méthode n'est pas utilisée pour le LLMValidator.
        
        Utiliser validate_anomalies() à la place.
        
        Args:
            metric: Non utilisé
            
        Returns:
            Liste vide
        """
        # Le LLMValidator ne détecte pas, il valide
        return []
    
    def validate_anomalies(
        self,
        anomalies: List[Anomaly],
        keep_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Valide et enrichit une liste d'anomalies avec le LLM.
        
        Args:
            anomalies: Anomalies à valider
            keep_all: Si True, garde toutes les anomalies (avec validation)
                      Si False, filtre les faux positifs
            
        Returns:
            Liste des anomalies enrichies avec analyse LLM
        """
        if not self.is_enabled():
            logger.debug("LLMValidator is disabled")
            return []
        
        if not self.llm_client:
            logger.warning("LLM client not available")
            return []
        
        if not anomalies:
            return []
        
        logger.info(f"Validating {len(anomalies)} anomalies with LLM...")
        
        validated_anomalies = []
        
        for anomaly in anomalies:
            try:
                # Convertir en dict
                anomaly_dict = anomaly.to_dict() if hasattr(anomaly, 'to_dict') else anomaly
                
                # Valider avec LLM
                llm_analysis = self.llm_client.validate_anomaly(anomaly_dict)
                
                # Enrichir l'anomalie
                enriched = {
                    **anomaly_dict,
                    'llm_validation': llm_analysis.get('llm_validation'),
                    'llm_analysis': llm_analysis.get('llm_analysis'),
                    'llm_model': llm_analysis.get('llm_model', 'mixtral-8x7b-32768')
                }
                
                # Décider si on garde l'anomalie
                if keep_all or self._should_keep_anomaly(enriched):
                    validated_anomalies.append(enriched)
                    
            except Exception as e:
                logger.error(f"Error validating anomaly: {e}")
                if keep_all:
                    validated_anomalies.append(anomaly_dict)
        
        logger.info(f"LLM validation completed: {len(validated_anomalies)} anomalies kept")
        return validated_anomalies
    
    def _should_keep_anomaly(self, anomaly: Dict[str, Any]) -> bool:
        """
        Décide si une anomalie doit être conservée basé sur l'analyse LLM.
        
        Args:
            anomaly: Anomalie avec analyse LLM
            
        Returns:
            True si l'anomalie doit être gardée, False sinon
        """
        # Si pas d'analyse LLM, garder par défaut (laisser les stats décider)
        if not anomaly.get('llm_analysis'):
            return True
        
        analysis = anomaly['llm_analysis'].lower()
        
        # Filtrer les réponses explicitement négatives
        negative_indicators = ['non', 'false positive', 'probably not', 'unlikely']
        
        for indicator in negative_indicators:
            if indicator in analysis:
                logger.warning(
                    f"LLM marked as potential false positive: {anomaly.get('metric_name')}"
                )
                return False
        
        return True
    
    def generate_smart_recommendations(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Génère des recommandations intelligentes basées sur l'analyse LLM.
        
        Args:
            anomalies: Anomalies validées
            
        Returns:
            Liste de recommandations
        """
        if not self.llm_client or not anomalies:
            return []
        
        recommendations = []
        
        for anomaly in anomalies:
            llm_analysis = anomaly.get('llm_analysis', '')
            
            if llm_analysis:
                # Extraire les recommandations du texte LLM
                if 'action' in llm_analysis.lower() or 'investigate' in llm_analysis.lower():
                    recommendations.append(f"[{anomaly.get('metric_name')}] {llm_analysis}")
        
        return recommendations
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"LLMValidator({status})"
