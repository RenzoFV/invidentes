"""
Utilidades para serialización JSON compatible con numpy y otros tipos.
"""

import json
import numpy as np
from typing import Any


def convert_to_serializable(obj: Any) -> Any:
    """
    Convierte objetos numpy y otros tipos no serializables a tipos nativos de Python.
    
    Args:
        obj: Objeto a convertir
        
    Returns:
        Objeto serializable
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj


def safe_json_dumps(obj: Any) -> str:
    """
    Serializa un objeto a JSON de forma segura, convirtiendo tipos numpy.
    
    Args:
        obj: Objeto a serializar
        
    Returns:
        String JSON
    """
    serializable_obj = convert_to_serializable(obj)
    return json.dumps(serializable_obj)

