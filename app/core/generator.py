from typing import Any, Dict, List, Set
from faker import Faker
import random

fake = Faker()

def find_dependencies(template: Any, prefix="$ref:") -> Set[str]:
    """Finds all model dependencies in a template based on the $ref format."""
    deps = set()
    if isinstance(template, dict):
        for v in template.values():
            deps.update(find_dependencies(v, prefix))
    elif isinstance(template, list):
        for item in template:
            deps.update(find_dependencies(item, prefix))
    elif isinstance(template, str) and template.startswith(prefix):
        # Format: "$ref:ModelName.field_name"
        parts = template[len(prefix):].split('.')
        if len(parts) >= 1:
            deps.add(parts[0])
    return deps

def resolve_ref(ref_string: str, context: Dict[str, List[Dict[str, Any]]], prefix="$ref:") -> Any:
    """Resolves a $ref string against the generated context."""
    path = ref_string[len(prefix):]
    parts = path.split('.')
    if len(parts) != 2:
        raise ValueError(f"Invalid reference format: {ref_string}. Expected $ref:ModelName.field_name")
        
    model_name, field_name = parts
    if model_name not in context or not context[model_name]:
        raise ValueError(f"Referenced model '{model_name}' has not been generated or is empty.")
        
    # Randomly pick an item from the already generated list for that model
    selected_item = random.choice(context[model_name])
    if field_name not in selected_item:
        raise ValueError(f"Field '{field_name}' not found in generated model '{model_name}'.")
        
    return selected_item[field_name]

def generate_mock_value(key: str, template_value: Any, context: Dict[str, List[Dict[str, Any]]]) -> Any:
    """
    Recursively generates mock data for a given key and template value.
    Infers the type of data to generate based on the value type and key name heuristics.
    Resolves relations if the value is a string starting with $ref:
    """
    # Handle nested structures
    if isinstance(template_value, dict):
        return {k: generate_mock_value(k, v, context) for k, v in template_value.items()}
    elif isinstance(template_value, list):
        if not template_value:
            return []
        item_template = template_value[0]
        return [generate_mock_value(key, item_template, context) for _ in range(len(template_value))]
    
    # Handle reference resolution
    if isinstance(template_value, str) and template_value.startswith("$ref:"):
        return resolve_ref(template_value, context)
    
    # Heuristics for Strings
    if isinstance(template_value, str):
        key_lower = key.lower()
        if 'email' in key_lower:
            return fake.email()
        elif 'first_name' in key_lower or 'firstname' in key_lower:
            return fake.first_name()
        elif 'last_name' in key_lower or 'lastname' in key_lower:
            return fake.last_name()
        elif 'name' in key_lower:
            return fake.name()
        elif 'address' in key_lower:
            return fake.address()
        elif 'city' in key_lower:
            return fake.city()
        elif 'state' in key_lower:
            return fake.state()
        elif 'country' in key_lower:
            return fake.country()
        elif 'zip' in key_lower or 'postal' in key_lower:
            return fake.zipcode()
        elif 'phone' in key_lower:
            return fake.phone_number()
        elif 'company' in key_lower:
            return fake.company()
        elif 'job' in key_lower or 'title' in key_lower:
            return fake.job()
        elif 'description' in key_lower or 'bio' in key_lower:
            return fake.text(max_nb_chars=200)
        elif 'date' in key_lower:
            return fake.date()
        elif 'time' in key_lower:
            return fake.time()
        elif 'url' in key_lower or 'website' in key_lower:
            return fake.url()
        elif 'uuid' in key_lower or ('id' in key_lower and key_lower != 'id'):
            return fake.uuid4()
        elif 'color' in key_lower:
            return fake.color_name()
        else:
            return fake.word()

    # Heuristics for Numbers
    elif isinstance(template_value, int) and not isinstance(template_value, bool):
        key_lower = key.lower()
        if 'id' == key_lower or 'id' in key_lower:
            return fake.random_int(min=1, max=999999)
        elif 'age' in key_lower:
            return fake.random_int(min=1, max=100)
        elif 'year' in key_lower:
            return int(fake.year())
        return fake.random_int(min=0, max=1000)
        
    elif isinstance(template_value, float):
        key_lower = key.lower()
        if 'price' in key_lower or 'amount' in key_lower or 'cost' in key_lower or 'balance' in key_lower:
            return round(fake.pyfloat(left_digits=3, right_digits=2, positive=True), 2)
        return fake.pyfloat(left_digits=3, right_digits=2)
        
    elif isinstance(template_value, bool):
        return fake.boolean()
        
    elif template_value is None:
        return None
        
    # Default fallback
    return fake.word()

def generate_mock_models(models_config: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Takes a dictionary mapping model names to their configurations (count, template)
    Resolves their dependency execution order, and generates the context dictionary.
    """
    # 1. Build Adjacency List for dependencies
    graph = {model_name: find_dependencies(config["template"]) for model_name, config in models_config.items()}
    
    # 2. Topological Sort to find execution order
    execution_order = []
    visited = set()
    temp_visited = set()
    
    def visit(node):
        if node in temp_visited:
            raise ValueError(f"Circular dependency detected involving model: {node}")
        if node not in visited:
            temp_visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in models_config:
                    raise ValueError(f"Model '{node}' depends on unknown model '{neighbor}'")
                visit(neighbor)
            temp_visited.remove(node)
            visited.add(node)
            execution_order.append(node)
            
    for model_name in models_config:
        if model_name not in visited:
            visit(model_name)
            
    # 3. Generate data in correct order
    context: Dict[str, List[Dict[str, Any]]] = {}
    for model_name in execution_order:
        config = models_config[model_name]
        count = config["count"]
        template = config["template"]
        
        generated_items = []
        for _ in range(count):
            mock_item = {k: generate_mock_value(k, v, context) for k, v in template.items()}
            generated_items.append(mock_item)
            
        context[model_name] = generated_items
        
    return context
