import re
import uuid
import string
import random
import hashlib
import json
from datetime import datetime
from faker import Faker
from typing import Any, Dict, List

fake = Faker()

def generate_random_string(length: int = 10, chars: str = string.ascii_letters + string.digits + string.punctuation) -> str:
    return ''.join(random.choice(chars) for _ in range(length))

def process_explicit_value(template_value: str) -> Any:
    """
    Parses a string rule and returns the generated data type.
    If it doesn't match a known rule, returns the string as-is.
    """
    if template_value == "STRING":
        return generate_random_string(15)
        
    if template_value == "STRING_NUMERIC":
        return generate_random_string(10, string.digits)
        
    if template_value == "STRING_ALPHA":
        return generate_random_string(10, string.ascii_letters)
        
    if template_value == "STRING_ALPHA_NUMERIC":
        return generate_random_string(15, string.ascii_letters + string.digits)
        
    if template_value == "INTEGER":
        return random.randint(0, 1000000)
        
    if template_value == "LONG":
        return random.randint(1000000000, 999999999999)
        
    # Check for TIMESTAMP(...)
    timestamp_match = re.match(r"^TIMESTAMP(?:\((.*)\))?$", template_value)
    if timestamp_match:
        dt = fake.date_time_between(start_date='-5y', end_date='now')
        format_str = timestamp_match.group(1)
        if format_str:
            return dt.strftime(format_str)
        return dt.isoformat()
        
    # Check for DECIMAL{N}
    decimal_match = re.match(r"^DECIMAL(\d+)$", template_value)
    if decimal_match:
        precision = int(decimal_match.group(1))
        # Generate a random float between 0 and 10000
        val = random.uniform(0.0, 10000.0)
        return round(val, precision)
        
    # UUID is handled post-generation as it requires hashing the payload
    # But if someone just wants a raw UUID field without hashing the whole payload payload:
    # We will let the post-processor handle "UUID" specifically.
    
    return template_value

def generate_explicit_mock_item(template: Any) -> Any:
    """
    Recursively generates mock data based strictly on string type definitions.
    """
    if isinstance(template, dict):
        return {k: generate_explicit_mock_item(v) for k, v in template.items()}
    elif isinstance(template, list):
        if not template:
            return []
            
        # If the template array has only 1 element, repeating that template 3 times is standard behavior
        if len(template) == 1:
            item_template = template[0]
            return [generate_explicit_mock_item(item_template) for _ in range(3)]
            
        # Otherwise, strictly generate the exact mocked sequence passed
        return [generate_explicit_mock_item(item) for item in template]
    elif isinstance(template, str):
        return process_explicit_value(template)
    
    # If it's an int, float, bool, or None, just return it as a literal exactly as it is.
    return template

def apply_post_generation_rules(item: Any) -> Any:
    """
    Applies rules that require the entire generated payload, such as hashing it into a UUID format.
    Recursively applies this down to sub-objects and arrays.
    """
    if isinstance(item, list):
        return [apply_post_generation_rules(child) for child in item]
        
    if not isinstance(item, dict):
        return item
        
    has_uuid_marker = False
    uuid_keys = []
    
    # Simple search for the "UUID" value marker
    for k, v in item.items():
        if v == "UUID":
            has_uuid_marker = True
            uuid_keys.append(k)
        elif isinstance(v, (dict, list)):
            item[k] = apply_post_generation_rules(v)
            
    if not has_uuid_marker:
        return item
        
    # Create a copy of the item without the UUID fields to hash
    hashable_payload = {k: v for k, v in item.items() if k not in uuid_keys}
    
    # Hash the payload to generate a reproducible "UUID" based on content
    payload_json_str = json.dumps(hashable_payload, sort_keys=True)
    md5_hash = hashlib.md5(payload_json_str.encode('utf-8')).hexdigest()
    
    # Format the MD5 hash into a UUID standard format (8-4-4-4-12)
    custom_uuid = f"{md5_hash[:8]}-{md5_hash[8:12]}-{md5_hash[12:16]}-{md5_hash[16:20]}-{md5_hash[20:]}"
    
    # Assign the hash to requested keys
    result = item.copy()
    for k in uuid_keys:
        result[k] = custom_uuid
        
    return result

def generate_explicit_models(models_config: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generates data mapping according to explicit type rules.
    Currently, explicit generator does not resolve $ref dependencies, it's a structural 1:1 generator.
    """
    context: Dict[str, List[Dict[str, Any]]] = {}
    
    for model_name, config in models_config.items():
        count = config["count"]
        template = config["template"]
        
        generated_items = []
        for _ in range(count):
            raw_item = generate_explicit_mock_item(template)
            
            # Since top-level is expected to be a dict, process post-generation rules
            if isinstance(raw_item, dict):
                processed_item = apply_post_generation_rules(raw_item)
            else:
                processed_item = raw_item
                
            generated_items.append(processed_item)
            
        context[model_name] = generated_items
        
    return context
