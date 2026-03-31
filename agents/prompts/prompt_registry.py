import json
import os
from typing import Dict, Any
from datetime import datetime

class PromptRegistry:
    """Versioned prompt management system"""
    
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'versions')
    
    @classmethod
    def get_prompt(cls, prompt_name: str, version: str = None) -> Dict[str, Any]:
        """Get a specific version of a prompt"""
        if version is None:
            version = cls.get_current_version(prompt_name)
        
        prompt_path = os.path.join(cls.PROMPTS_DIR, f"{prompt_name}_{version}.json")
        with open(prompt_path, 'r') as f:
            return json.load(f)
    
    @classmethod
    def get_current_version(cls, prompt_name: str) -> str:
        """Get the current active version"""
        config_path = os.path.join(cls.PROMPTS_DIR, 'current.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get(prompt_name, 'v1')
    
    @classmethod
    def register_prompt(cls, prompt_name: str, version: str, prompt_data: Dict):
        """Register a new prompt version"""
        prompt_path = os.path.join(cls.PROMPTS_DIR, f"{prompt_name}_{version}.json")
        with open(prompt_path, 'w') as f:
            json.dump(prompt_data, f, indent=2)