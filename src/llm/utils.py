import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger("CloudCull.LLM.Utils")

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Industrial-grade JSON extraction from LLM output.
    Handles markdown blocks, prefix text, and common formatting artifacts.
    """
    if not text:
        return {}
        
    text_clean = text.strip()
    
    # 1. Strip Markdown Code Blocks
    if "```" in text_clean:
        # Match content between ```json ... ``` or just ``` ... ```
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(pattern, text_clean, re.DOTALL | re.IGNORECASE)
        if match:
            text_clean = match.group(1).strip()
    
    # 2. Find the JSON Object bound by {}
    # We look for the first '{' and the last '}'
    start_idx = text_clean.find('{')
    end_idx = text_clean.rfind('}')
    
    if start_idx != -1 and end_idx != -1:
        json_str = text_clean[start_idx : end_idx + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e} | Content: {json_str[:100]}...")
            # 3. Last Resort: Simple regex for basic keys if JSON is mangled but keys exist
            # This is a bit risky but can save some cases
            return {}
    
    return {}
