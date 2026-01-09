"""
Data validators for Hospital-E
Validates JSON schemas and data integrity
"""
from typing import Dict, Any, List
from datetime import datetime
import re


class ValidationError(Exception):
    """Custom validation error"""
    pass


class SchemaValidator:
    """Validates data against JSON schemas"""
    
    @staticmethod
    def validate_inventory_low_event(data: Dict[str, Any]) -> bool:
        """
        Validate InventoryLowEvent schema
        Schema: contracts/schemas/InventoryLowEvent.schema.json
        
        Args:
            data: Event data dictionary
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        required_fields = [
            'eventId', 'eventType', 'hospitalId', 'productCode',
            'currentStockUnits', 'dailyConsumptionUnits', 
            'daysOfSupply', 'threshold', 'timestamp'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate eventType
        if data['eventType'] != 'InventoryLow':
            raise ValidationError(f"Invalid eventType: {data['eventType']}")
        
        # Validate data types
        if not isinstance(data['currentStockUnits'], int):
            raise ValidationError("currentStockUnits must be integer")
        
        if not isinstance(data['dailyConsumptionUnits'], int):
            raise ValidationError("dailyConsumptionUnits must be integer")
        
        if not isinstance(data['daysOfSupply'], (int, float)):
            raise ValidationError("daysOfSupply must be number")
        
        if not isinstance(data['threshold'], (int, float)):
            raise ValidationError("threshold must be number")
        
        # Validate ranges
        if data['currentStockUnits'] < 0:
            raise ValidationError("currentStockUnits must be >= 0")
        
        if data['dailyConsumptionUnits'] < 0:
            raise ValidationError("dailyConsumptionUnits must be >= 0")
        
        if data['daysOfSupply'] < 0:
            raise ValidationError("daysOfSupply must be >= 0")
        
        if data['threshold'] < 0:
            raise ValidationError("threshold must be >= 0")
        
        # Validate timestamp format (ISO 8601)
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Invalid timestamp format (must be ISO 8601)")
        
        return True
    
    @staticmethod
    def validate_order_creation_command(data: Dict[str, Any]) -> bool:
        """
        Validate OrderCreationCommand schema
        Schema: contracts/schemas/OrderCreationCommand.schema.json
        
        Args:
            data: Command data dictionary
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        required_fields = [
            'commandId', 'commandType', 'orderId', 'hospitalId',
            'productCode', 'orderQuantity', 'priority',
            'estimatedDeliveryDate', 'timestamp'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate commandType
        if data['commandType'] != 'CreateOrder':
            raise ValidationError(f"Invalid commandType: {data['commandType']}")
        
        # Validate priority
        valid_priorities = ['URGENT', 'HIGH', 'NORMAL']
        if data['priority'] not in valid_priorities:
            raise ValidationError(
                f"Invalid priority: {data['priority']}. "
                f"Must be one of: {valid_priorities}"
            )
        
        # Validate data types
        if not isinstance(data['orderQuantity'], int):
            raise ValidationError("orderQuantity must be integer")
        
        # Validate ranges
        if data['orderQuantity'] <= 0:
            raise ValidationError("orderQuantity must be > 0")
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Invalid timestamp format")
        
        # Validate estimated delivery date
        try:
            datetime.fromisoformat(
                data['estimatedDeliveryDate'].replace('Z', '+00:00')
            )
        except ValueError:
            raise ValidationError("Invalid estimatedDeliveryDate format")
        
        return True


class DataValidator:
    """General data validation utilities"""
    
    @staticmethod
    def validate_hospital_id(hospital_id: str) -> bool:
        """Validate hospital ID format"""
        pattern = r'^[A-Z][a-zA-Z0-9\-]+$'
        if not re.match(pattern, hospital_id):
            raise ValidationError(
                f"Invalid hospital ID format: {hospital_id}"
            )
        return True
    
    @staticmethod
    def validate_product_code(product_code: str) -> bool:
        """Validate product code format"""
        pattern = r'^[A-Z0-9\-]+$'
        if not re.match(pattern, product_code):
            raise ValidationError(
                f"Invalid product code format: {product_code}"
            )
        return True
    
    @staticmethod
    def validate_stock_values(
        current_stock: int,
        daily_consumption: int,
        days_of_supply: float
    ) -> bool:
        """Validate stock-related values"""
        if current_stock < 0:
            raise ValidationError("Stock cannot be negative")
        
        if daily_consumption < 0:
            raise ValidationError("Daily consumption cannot be negative")
        
        if days_of_supply < 0:
            raise ValidationError("Days of supply cannot be negative")
        
        # Verify calculation
        if daily_consumption > 0:
            calculated_days = current_stock / daily_consumption
            if abs(calculated_days - days_of_supply) > 0.1:
                raise ValidationError(
                    f"Days of supply mismatch: expected {calculated_days:.2f}, "
                    f"got {days_of_supply:.2f}"
                )
        
        return True
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Basic SQL injection prevention
        (psycopg2 handles this, but extra safety)
        """
        # Remove potential SQL injection patterns
        dangerous_patterns = [
            '--', ';--', '/*', '*/', 'xp_', 'sp_', 
            'DROP', 'DELETE', 'INSERT', 'UPDATE'
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in value.lower():
                raise ValidationError(
                    f"Invalid characters in input: {pattern}"
                )
        
        return value


# Singleton instances
schema_validator = SchemaValidator()
data_validator = DataValidator()