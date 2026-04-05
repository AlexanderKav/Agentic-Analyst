"""
Question Classifier - Detects question type and extracts time periods.
Single responsibility: Understand what the user is asking.
"""

import re
from typing import Dict, List, Optional, Tuple


class QuestionClassifier:
    """
    Classify questions and extract parameters.
    
    Features:
    - Multi-class question classification
    - Time period extraction (quarters, years, months)
    - Recommended tools based on question type
    - Support for natural language date parsing
    """
    
    # Question type keywords with weights for better accuracy
    QUESTION_TYPES: Dict[str, List[str]] = {
        'forecast': [
            'forecast', 'predict', 'future', 'will be', 'will look',
            'projection', 'estimate', 'expected', 'anticipate',
            'next year', 'coming year', '2025', '2026', '2027',
            'q1', 'q2', 'q3', 'q4', 'quarter',
            'first quarter', 'second quarter', 'third quarter', 'fourth quarter',
            'most likely', 'likely to be', 'projected', 'outlook'
        ],
        'risk': [
            'risk', 'risks', 'concern', 'threat', 'vulnerability',
            'danger', 'issue', 'problem', 'challenge', 'exposure',
            'downside', 'warning', 'alert', 'red flag', 'critical',
            'urgent', 'at risk', 'vulnerable', 'anomaly', 'anomalies',
            'outlier', 'outliers', 'unusual', 'strange', 'weird'
        ],
        'performance': [
            'performance', 'overview', 'dashboard', 'summary',
            'how is', 'how are', 'doing', 'health', 'status',
            'business performance', 'company performance', 'metrics',
            'kpi', 'kpis', 'scorecard', 'health check', 'snapshot'
        ],
        'revenue_analysis': [
            'revenue', 'sales', 'profit', 'income', 'earnings',
            'product', 'customer', 'region', 'top', 'best', 'worst',
            'ranking', 'rank', 'trend', 'growth', 'decline',
            'revenue breakdown', 'revenue by', 'sales by',
            'total revenue', 'average revenue', 'revenue growth',
            'show', 'tell', 'what is', 'how much', 'calculate',
            'sum', 'total', 'average', 'count'
        ],
        'customer_analysis': [
            'customer', 'client', 'buyer', 'account',
            'customer behavior', 'purchase pattern', 'retention',
            'churn', 'lifetime value', 'ltv', 'acquisition',
            'customer segment', 'customer group'
        ],
        'product_analysis': [
            'product', 'item', 'sku', 'inventory', 'stock',
            'product performance', 'product success', 'product health',
            'product category', 'product line'
        ]
    }
    
    # Time period patterns with extraction logic
    PERIOD_PATTERNS: List[Tuple[str, str]] = [
        (r'Q([1-4])\s*(\d{4})', 'quarter'),
        (r'(first|second|third|fourth)\s+quarter\s+of\s+(\d{4})', 'quarter_text'),
        (r'\b(20\d{2})\b', 'year'),
        (r'first\s+half\s+of\s+(\d{4})', 'half_year'),
        (r'second\s+half\s+of\s+(\d{4})', 'half_year'),
        (r'next\s+(\d+)\s+months?', 'months'),
        (r'next\s+(\d+)\s+quarters?', 'quarters'),
        (r'next\s+quarter', 'next_quarter'),
        (r'this\s+year', 'this_year'),
        (r'this\s+quarter', 'this_quarter'),
        (r'current\s+year', 'this_year'),
        (r'current\s+quarter', 'this_quarter'),
        (r'(\d{4})\s*-\s*(\d{4})', 'year_range'),
        (r'(\d{4})\s+to\s+(\d{4})', 'year_range'),
        (r'next\s+year', 'next_year'),
        (r'the\s+coming\s+year', 'next_year'),
        (r'next\s+month', 'next_month'),
        (r'last\s+month', 'last_month'),
        (r'last\s+quarter', 'last_quarter'),
        (r'last\s+year', 'last_year'),
        (r'previous\s+quarter', 'last_quarter'),
        (r'previous\s+year', 'last_year'),
    ]
    
    # Month mapping for text quarters
    QUARTER_MONTHS: Dict[str, str] = {
        'first': 'Q1',
        'second': 'Q2',
        'third': 'Q3',
        'fourth': 'Q4'
    }
    
    # Question type priority for ambiguous queries
    TYPE_PRIORITY: List[str] = [
        'forecast', 'risk', 'performance', 'revenue_analysis',
        'customer_analysis', 'product_analysis'
    ]
    
    def __init__(self):
        """Initialize the Question Classifier."""
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), period_type)
            for pattern, period_type in self.PERIOD_PATTERNS
        ]
        self._data_columns = None
    
    def set_data_columns(self, columns: List[str]):
        """Set the data columns for relevance checking."""
        self._data_columns = [col.lower() for col in columns] if columns else []
    
    def _has_business_context(self, question: str) -> bool:
        """Check if question has business context or matches data columns."""
        question_lower = question.lower()
        
        if self._data_columns:
            for col in self._data_columns:
                if col in question_lower:
                    return True
                if col.endswith('s') and col[:-1] in question_lower:
                    return True
                if not col.endswith('s') and col + 's' in question_lower:
                    return True
        
        business_keywords = [
            'revenue', 'sales', 'profit', 'customer', 'product', 
            'region', 'trend', 'growth', 'decline', 'forecast',
            'predict', 'anomaly', 'kpi', 'metric', 'performance',
            'show', 'tell', 'what', 'how', 'which', 'when', 'where',
            'total', 'average', 'sum', 'count', 'calculate', 'compute'
        ]
        
        return any(kw in question_lower for kw in business_keywords)
    
    def classify(self, question: Optional[str]) -> str:
        """
        Classify the question type.
        
        Returns:
            'relevant' if the question is about business data,
            'irrelevant' otherwise
        """
        if not question or not question.strip():
            return 'irrelevant'
        
        question_lower = question.lower().strip()
        
        # Very short questions are likely irrelevant
        if len(question_lower) < 3:
            return 'irrelevant'
        
        # Count matches for each type
        scores: Dict[str, int] = {}
        
        for qtype, keywords in self.QUESTION_TYPES.items():
            score = sum(1 for kw in keywords if kw in question_lower)
            if score > 0:
                scores[qtype] = score
        
        # If no matches in our types, check for business context
        if not scores:
            if self._has_business_context(question_lower):
                return 'revenue_analysis'  # Default to revenue analysis
            return 'irrelevant'
        
        # Get the highest scoring type
        highest_score = max(scores.values())
        top_types = [t for t, s in scores.items() if s == highest_score]
        
        # If tie, use priority order
        if len(top_types) > 1:
            for priority_type in self.TYPE_PRIORITY:
                if priority_type in top_types:
                    return priority_type
        
        return top_types[0] if top_types else 'revenue_analysis'
    
    def is_relevant(self, question: Optional[str]) -> bool:
        """Check if the question is relevant to business data analysis."""
        if not question:
            return False
        
        result = self.classify(question)
        return result != 'irrelevant'
    
    def get_irrelevant_response(self, question: Optional[str] = None) -> str:
        """
        Get the ONE generic response for ANY irrelevant question.
        (URLs, gibberish, random text, greetings, etc. all get the same response)
        """
        return (
            "I'm a business analytics assistant. I can only answer questions about your business data.\n\n"
            "Here are some examples of questions I can help with:\n"
            "• 'Show me revenue by product'\n"
            "• 'What are the sales trends over time?'\n"
            "• 'Forecast revenue for next quarter'\n"
            "• 'Which customers generate the most revenue?'\n"
            "• 'Detect anomalies in the data'\n\n"
            "Please ask a question related to your business data."
        )
    
    def extract_period(self, question: Optional[str]) -> Optional[str]:
        """Extract time period from question."""
        if not question:
            return None
        
        for pattern, period_type in self._compiled_patterns:
            match = pattern.search(question)
            if match:
                return self._format_period(match, period_type)
        
        return None
    
    def extract_all_periods(self, question: Optional[str]) -> List[str]:
        """Extract all time periods from question."""
        if not question:
            return []
        
        periods = []
        for pattern, period_type in self._compiled_patterns:
            matches = pattern.findall(question)
            for match in matches:
                if isinstance(match, tuple):
                    mock_match = type('MockMatch', (), {'group': lambda self, x: match[x-1] if x <= len(match) else None})()
                    period = self._format_period(mock_match, period_type)
                    if period not in periods:
                        periods.append(period)
                else:
                    periods.append(match)
        
        return periods
    
    def _format_period(self, match, period_type: str) -> str:
        """Format extracted period into standard string."""
        period_map = {
            'quarter': lambda m: f"Q{m.group(1)} {m.group(2)}",
            'quarter_text': lambda m: f"{self.QUARTER_MONTHS.get(m.group(1).lower(), m.group(1))} {m.group(2)}",
            'year': lambda m: m.group(1),
            'year_range': lambda m: f"{m.group(1)}-{m.group(2)}",
            'next_year': lambda m: "next_year",
            'next_quarter': lambda m: "next_quarter",
            'next_month': lambda m: "next_month",
            'last_month': lambda m: "last_month",
            'last_quarter': lambda m: "last_quarter",
            'last_year': lambda m: "last_year",
            'this_year': lambda m: "this_year",
            'this_quarter': lambda m: "this_quarter",
            'half_year': lambda m: f"H{1 if 'first' in match.string.lower() else 2} {m.group(1)}",
            'months': lambda m: f"next {m.group(1)} months",
            'quarters': lambda m: f"next {m.group(1)} quarters",
        }
        
        formatter = period_map.get(period_type)
        if formatter:
            return formatter(match)
        
        return match.group(0) if hasattr(match, 'group') else str(match)
    
    def get_recommended_tools(self, question_type: str) -> List[str]:
        """Get recommended tools based on question type."""
        base_tools = ['compute_kpis', 'visualization']
        
        tool_mapping = {
            'forecast': [
                'monthly_revenue_by_product',
                'monthly_growth',
                'revenue_by_product',
                'forecast_revenue_by_product'
            ],
            'risk': [
                'detect_revenue_spikes',
                'revenue_by_payment_status',
                'monthly_revenue_by_product'
            ],
            'performance': [
                'revenue_by_product',
                'revenue_by_region',
                'revenue_by_customer',
                'monthly_growth'
            ],
            'revenue_analysis': [
                'revenue_by_product',
                'revenue_by_region',
                'revenue_by_customer',
                'monthly_revenue_by_product'
            ],
            'customer_analysis': [
                'revenue_by_customer',
                'monthly_revenue_by_customer'
            ],
            'product_analysis': [
                'revenue_by_product',
                'monthly_revenue_by_product'
            ],
            'overview': [
                'revenue_by_product',
                'revenue_by_customer',
                'monthly_revenue_by_product',
                'detect_revenue_spikes'
            ],
        }
        
        tools = tool_mapping.get(question_type, tool_mapping.get('revenue_analysis', []))
        
        seen = set()
        result = []
        for tool in base_tools + tools:
            if tool not in seen:
                seen.add(tool)
                result.append(tool)
        
        return result
    
    def has_forecast_intent(self, question: Optional[str]) -> bool:
        """Check if question has forecast/prediction intent."""
        if not question:
            return False
        
        forecast_indicators = [
            'forecast', 'predict', 'future', 'will be', 'project',
            'estimate', 'expected', 'anticipate', 'outlook'
        ]
        question_lower = question.lower()
        return any(indicator in question_lower for indicator in forecast_indicators)
    
    def has_risk_intent(self, question: Optional[str]) -> bool:
        """Check if question has risk/concern intent."""
        if not question:
            return False
        
        risk_indicators = [
            'risk', 'concern', 'threat', 'danger', 'issue',
            'problem', 'challenge', 'warning', 'alert',
            'anomaly', 'outlier', 'unusual', 'strange'
        ]
        question_lower = question.lower()
        return any(indicator in question_lower for indicator in risk_indicators)
    
    def get_question_confidence(self, question: Optional[str]) -> float:
        """Get confidence score for the classification."""
        if not question:
            return 0.0
        
        question_lower = question.lower()
        total_matches = 0
        type_matches = 0
        
        for qtype, keywords in self.QUESTION_TYPES.items():
            matches = sum(1 for kw in keywords if kw in question_lower)
            total_matches += matches
            if matches > 0:
                type_matches += matches
        
        if total_matches == 0:
            return 0.0
        
        return min(1.0, type_matches / total_matches)
    
    def get_question_summary(self, question: Optional[str]) -> Dict:
        """Get a comprehensive summary of the question analysis."""
        return {
            'question': question,
            'type': self.classify(question),
            'is_relevant': self.is_relevant(question),
            'period': self.extract_period(question),
            'all_periods': self.extract_all_periods(question),
            'has_forecast': self.has_forecast_intent(question),
            'has_risk': self.has_risk_intent(question),
            'confidence': self.get_question_confidence(question),
            'recommended_tools': self.get_recommended_tools(self.classify(question))
        }


__all__ = ['QuestionClassifier']