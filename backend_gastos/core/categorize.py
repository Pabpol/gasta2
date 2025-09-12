"""
Expense categorization using merchant mapping, rules, and optional ML.
Provides intelligent categorization with confidence scoring.
"""
import pandas as pd
import re
import yaml
import logging
from typing import Dict, Tuple, Optional, Any, List
from pathlib import Path
import unicodedata

from .paths import MERCHANT_MAP, CONFIG_YAML, MODEL_PATH

# Configure logging
logger = logging.getLogger(__name__)

def normalize_text(s: str) -> str:
    """Normalize text for better matching"""
    if not isinstance(s, str):
        return ""
    
    # Convert to lowercase
    s = s.lower()
    
    # Remove accents
    s = unicodedata.normalize('NFD', s)
    s = ''.join(char for char in s if unicodedata.category(char) != 'Mn')
    
    # Remove special characters except spaces
    s = re.sub(r'[^\w\s]', ' ', s)
    
    # Remove extra whitespace
    s = ' '.join(s.split())
    
    return s.strip()

class Categorizer:
    """Intelligent expense categorization system"""
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.merchant_map = {}
        self.rules = {}
        self.ml_model = None
        self.ml_vectorizer = None
        
        self._load_merchant_map()
        self._load_config()
        self._load_ml_model()
    
    def _load_merchant_map(self):
        """Load merchant mapping from CSV"""
        try:
            if MERCHANT_MAP.exists():
                df = pd.read_csv(MERCHANT_MAP)
                for _, row in df.iterrows():
                    merchant = normalize_text(str(row.get('merchant', '')))
                    categoria = str(row.get('categoria', ''))
                    subcategoria = str(row.get('subcategoria', ''))
                    
                    if merchant and categoria:
                        self.merchant_map[merchant] = {
                            'categoria': categoria,
                            'subcategoria': subcategoria
                        }
                logger.info(f"Loaded {len(self.merchant_map)} merchant mappings")
            else:
                logger.info("No merchant map file found")
        except Exception as e:
            logger.error(f"Error loading merchant map: {e}")
    
    def _load_config(self):
        """Load categorization rules from YAML config"""
        try:
            if CONFIG_YAML.exists():
                with open(CONFIG_YAML, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self.rules = config.get('categorization_rules', {})
                logger.info(f"Loaded {len(self.rules)} categorization rules")
            else:
                # Default rules
                self.rules = {
                    'transporte': {
                        'keywords': ['uber', 'taxi', 'metro', 'bus', 'transantiago', 'bip'],
                        'subcategoria': 'transporte_publico'
                    },
                    'alimentacion': {
                        'keywords': ['restaurant', 'comida', 'delivery', 'rappi', 'pedidos', 'mcdonalds', 'burger'],
                        'subcategoria': 'restaurantes'
                    },
                    'supermercado': {
                        'keywords': ['jumbo', 'lider', 'santa isabel', 'tottus', 'unimarc'],
                        'subcategoria': 'supermercado'
                    },
                    'combustible': {
                        'keywords': ['copec', 'shell', 'petrobras', 'esso', 'combustible'],
                        'subcategoria': 'gasolina'
                    },
                    'servicios': {
                        'keywords': ['netflix', 'spotify', 'internet', 'telefono', 'luz', 'agua', 'gas'],
                        'subcategoria': 'suscripciones'
                    }
                }
                logger.info("Using default categorization rules")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.rules = {}
    
    def _load_ml_model(self):
        """Load ML model if available"""
        try:
            if MODEL_PATH.exists():
                import joblib
                model_data = joblib.load(MODEL_PATH)
                self.ml_model = model_data.get('model')
                self.ml_vectorizer = model_data.get('vectorizer')
                logger.info("ML model loaded successfully")
            else:
                logger.info("No ML model found")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
    
    def add_merchant_alias(self, merchant_text: str, categoria: str, subcategoria: str = ""):
        """Add a new merchant alias to the mapping"""
        normalized = normalize_text(merchant_text)
        self.merchant_map[normalized] = {
            'categoria': categoria,
            'subcategoria': subcategoria
        }
        
        # Save to CSV if file exists
        try:
            if MERCHANT_MAP.exists():
                df = pd.read_csv(MERCHANT_MAP)
            else:
                df = pd.DataFrame(columns=['merchant', 'categoria', 'subcategoria'])
            
            new_row = pd.DataFrame([{
                'merchant': merchant_text,
                'categoria': categoria,
                'subcategoria': subcategoria
            }])
            
            df = pd.concat([df, new_row], ignore_index=True)
            df.drop_duplicates(subset=['merchant'], keep='last', inplace=True)
            df.to_csv(MERCHANT_MAP, index=False)
            logger.info(f"Added merchant alias: {merchant_text} -> {categoria}")
            
        except Exception as e:
            logger.error(f"Error saving merchant alias: {e}")
    
    def _match_merchant(self, description: str) -> Optional[Tuple[str, str, float]]:
        """Try to match against merchant mapping"""
        normalized_desc = normalize_text(description)
        
        # Exact match first
        if normalized_desc in self.merchant_map:
            mapping = self.merchant_map[normalized_desc]
            return mapping['categoria'], mapping['subcategoria'], 1.0
        
        # Partial match
        for merchant, mapping in self.merchant_map.items():
            if merchant in normalized_desc or normalized_desc in merchant:
                return mapping['categoria'], mapping['subcategoria'], 0.9
        
        return None
    
    def _match_rules(self, description: str) -> Optional[Tuple[str, str, float]]:
        """Try to match against keyword rules"""
        normalized_desc = normalize_text(description)
        
        for categoria, rule in self.rules.items():
            keywords = rule.get('keywords', [])
            for keyword in keywords:
                if normalize_text(keyword) in normalized_desc:
                    subcategoria = rule.get('subcategoria', '')
                    return categoria, subcategoria, 0.8
        
        return None
    
    def _ml_predict(self, description: str) -> Optional[Tuple[str, str, float]]:
        """Use ML model for prediction"""
        if not self.ml_model or not self.ml_vectorizer:
            return None
        
        try:
            # Transform text
            features = self.ml_vectorizer.transform([description])
            
            # Predict
            prediction = self.ml_model.predict(features)[0]
            confidence = max(self.ml_model.predict_proba(features)[0])
            
            if confidence >= self.threshold:
                # Assuming prediction format is "categoria|subcategoria"
                if '|' in prediction:
                    categoria, subcategoria = prediction.split('|', 1)
                else:
                    categoria, subcategoria = prediction, ""
                
                return categoria, subcategoria, confidence
        
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
        
        return None
    
    def categorize_one(self, gasto: Dict[str, Any]) -> Tuple[str, str, str, float]:
        """
        Categorize a single expense
        Returns: (categoria, subcategoria, estado, confianza)
        """
        description = str(gasto.get('descripcion', ''))
        
        if not description.strip():
            return "", "", "pendiente", 0.0
        
        # Try merchant mapping first
        result = self._match_merchant(description)
        if result:
            categoria, subcategoria, confidence = result
            estado = "categorizado" if confidence >= self.threshold else "pendiente"
            return categoria, subcategoria, estado, confidence
        
        # Try rule-based matching
        result = self._match_rules(description)
        if result:
            categoria, subcategoria, confidence = result
            estado = "categorizado" if confidence >= self.threshold else "pendiente"
            return categoria, subcategoria, estado, confidence
        
        # Try ML prediction
        result = self._ml_predict(description)
        if result:
            categoria, subcategoria, confidence = result
            estado = "categorizado" if confidence >= self.threshold else "pendiente"
            return categoria, subcategoria, estado, confidence
        
        # No match found
        return "", "", "pendiente", 0.0
    
    def get_category_suggestions(self, description: str, limit: int = 5) -> List[str]:
        """Get category suggestions for manual categorization"""
        # Common categories based on typical expenses
        common_categories = [
            "alimentacion", "transporte", "supermercado", "combustible",
            "servicios", "salud", "entretenimiento", "ropa", "hogar",
            "educacion", "deportes", "tecnologia", "comercio_electronico", 
            "viajes", "otros"
        ]
        
        # Try to find relevant categories based on description
        normalized_desc = normalize_text(description)
        suggestions = []
        
        # Check rules for relevant categories
        for categoria, rule in self.rules.items():
            keywords = rule.get('keywords', [])
            for keyword in keywords:
                if normalize_text(keyword) in normalized_desc:
                    if categoria not in suggestions:
                        suggestions.append(categoria)
        
        # Add common categories that aren't already suggested
        for cat in common_categories:
            if cat not in suggestions and len(suggestions) < limit:
                suggestions.append(cat)
        
        return suggestions[:limit]
