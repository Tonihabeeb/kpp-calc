"""
Configuration Schema for KPP Simulator
Defines configuration schema and validation rules
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Type, Tuple
from enum import Enum
import json
import os

class SchemaType(Enum):
    """Schema data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"

@dataclass
class SchemaField:
    """Schema field definition"""
    name: str
    field_type: SchemaType
    required: bool = False
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""

class ConfigSchema:
    """Configuration schema manager"""
    
    def __init__(self):
        """Initialize configuration schema"""
        self.schema_data: Dict[str, Dict[str, SchemaField]] = {}
        self.validation_errors: List[str] = []
        
    def load_schema(self, schema_path: str) -> bool:
        """Load schema from file"""
        try:
            if not os.path.exists(schema_path):
                return False
                
            with open(schema_path, 'r') as f:
                schema_json = json.load(f)
                
            for component, fields in schema_json.items():
                self.schema_data[component] = {}
                for field_name, field_def in fields.items():
                    self.schema_data[component][field_name] = SchemaField(
                        name=field_name,
                        field_type=SchemaType(field_def['type']),
                        required=field_def.get('required', False),
                        default=field_def.get('default'),
                        min_value=field_def.get('min_value'),
                        max_value=field_def.get('max_value'),
                        allowed_values=field_def.get('allowed_values'),
                        description=field_def.get('description', '')
                    )
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Failed to load schema: {e}")
            return False
    
    def validate_config(self, component: str, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration against schema"""
        self.validation_errors = []
        
        if component not in self.schema_data:
            self.validation_errors.append(f"Unknown component: {component}")
            return False, self.validation_errors
        
        schema = self.schema_data[component]
        
        # Check required fields
        for field_name, field_def in schema.items():
            if field_def.required and field_name not in config_data:
                self.validation_errors.append(
                    f"Required field missing: {field_name}"
                )
        
        # Validate field values
        for field_name, value in config_data.items():
            if field_name not in schema:
                self.validation_errors.append(
                    f"Unknown field: {field_name}"
                )
                continue
                
            field_def = schema[field_name]
            
            # Type validation
            if not self._validate_type(value, field_def.field_type, field_def.allowed_values):
                self.validation_errors.append(
                    f"Invalid type for {field_name}: expected {field_def.field_type.value}"
                )
            
            # Range validation
            if field_def.min_value is not None and value < field_def.min_value:
                self.validation_errors.append(
                    f"Value for {field_name} below minimum: {value} < {field_def.min_value}"
                )
            
            if field_def.max_value is not None and value > field_def.max_value:
                self.validation_errors.append(
                    f"Value for {field_name} above maximum: {value} > {field_def.max_value}"
                )
            
            # Allowed values validation
            if field_def.allowed_values is not None and value not in field_def.allowed_values:
                self.validation_errors.append(
                    f"Invalid value for {field_name}: {value} not in {field_def.allowed_values}"
                )
        
        return len(self.validation_errors) == 0, self.validation_errors
    
    def _validate_type(self, value: Any, expected_type: SchemaType, allowed_values: Optional[List[Any]] = None) -> bool:
        """Validate value type"""
        if expected_type == SchemaType.STRING:
            return isinstance(value, str)
        elif expected_type == SchemaType.INTEGER:
            return isinstance(value, int)
        elif expected_type == SchemaType.FLOAT:
            return isinstance(value, (int, float))
        elif expected_type == SchemaType.BOOLEAN:
            return isinstance(value, bool)
        elif expected_type == SchemaType.ARRAY:
            return isinstance(value, list)
        elif expected_type == SchemaType.OBJECT:
            return isinstance(value, dict)
        elif expected_type == SchemaType.ENUM:
            return isinstance(value, str) and allowed_values is not None and value in allowed_values
        return False
    
    def get_field_schema(self, component: str, field_name: str) -> Optional[SchemaField]:
        """Get schema for specific field"""
        if component not in self.schema_data:
            return None
        return self.schema_data[component].get(field_name)
    
    def get_component_schema(self, component: str) -> Optional[Dict[str, SchemaField]]:
        """Get schema for component"""
        return self.schema_data.get(component) 