"""Document field extraction utilities."""
import logging
from typing import Any, Dict, List, Optional, Set

from app.constants import EXPECTED_FIELDS, NOT_FOUND, EMPTY
from app.models import FieldData

logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extracts fields from Azure Document Intelligence results."""
    
    @staticmethod
    def normalize_field_name(field_name: str) -> str:
        """
        Normalize field name for comparison (case-insensitive, remove special chars).
        
        Args:
            field_name: Original field name
            
        Returns:
            Normalized field name
        """
        return field_name.replace(" ", "").replace("_", "").replace("-", "").lower()
    
    @staticmethod
    def match_expected_field(normalized_field: str, expected_fields: Set[str]) -> Optional[str]:
        """
        Match normalized field name with expected fields.
        
        Args:
            normalized_field: Normalized field name to match
            expected_fields: Set of expected field names
            
        Returns:
            Matched expected field name or None
        """
        for expected_field in expected_fields:
            normalized_expected = FieldExtractor.normalize_field_name(expected_field)
            if normalized_field == normalized_expected:
                return expected_field
        return None
    
    @staticmethod
    def extract_field_data(field_name: str, field_value: Any) -> Optional[FieldData]:
        """
        Extract data from a field value object.
        
        Args:
            field_name: Name of the field
            field_value: Field value object from Azure API
            
        Returns:
            FieldData object or None if extraction fails
        """
        confidence = None
        field_value_str = None
        
        # Get confidence if available
        if hasattr(field_value, 'confidence') and field_value.confidence is not None:
            confidence = round(field_value.confidence * 100, 2)
        
        # Priority 1: Try 'content' first (most reliable)
        if hasattr(field_value, 'content') and field_value.content:
            field_value_str = str(field_value.content).strip()
        
        # Priority 2: Try valueString (camelCase) or value_string (snake_case)
        elif hasattr(field_value, 'valueString') and field_value.valueString:
            field_value_str = str(field_value.valueString).strip()
        elif hasattr(field_value, 'value_string') and field_value.value_string:
            field_value_str = str(field_value.value_string).strip()
        
        # Priority 3: Try other value types
        elif hasattr(field_value, 'valueNumber') and field_value.valueNumber is not None:
            field_value_str = str(field_value.valueNumber)
        elif hasattr(field_value, 'value_number') and field_value.value_number is not None:
            field_value_str = str(field_value.value_number)
        elif hasattr(field_value, 'valueDate') and field_value.valueDate:
            field_value_str = str(field_value.valueDate)
        elif hasattr(field_value, 'value_date') and field_value.value_date:
            field_value_str = str(field_value.value_date)
        elif hasattr(field_value, 'valueCurrency') and field_value.valueCurrency:
            currency = field_value.valueCurrency
            if hasattr(currency, 'amount') and hasattr(currency, 'currencySymbol'):
                field_value_str = f"{currency.currencySymbol}{currency.amount}"
            elif hasattr(currency, 'amount') and hasattr(currency, 'currency_symbol'):
                field_value_str = f"{currency.currency_symbol}{currency.amount}"
            else:
                field_value_str = str(currency)
        elif hasattr(field_value, 'valueAddress') and field_value.valueAddress:
            address = field_value.valueAddress
            if hasattr(address, 'formatted'):
                field_value_str = address.formatted
            else:
                field_value_str = str(address)
        
        if field_value_str:
            return FieldData(
                field_name=field_name,
                field_value=field_value_str,
                confidence=confidence
            )
        return None
    
    @staticmethod
    def extract_from_structured_documents(
        analyze_result: Any,
        expected_fields: Set[str],
        found_fields: Set[str]
    ) -> List[FieldData]:
        """
        Extract fields from structured documents (invoices, receipts, etc.).
        
        Args:
            analyze_result: Result from Azure Document Intelligence
            expected_fields: Set of expected field names
            found_fields: Set to track found fields
            
        Returns:
            List of extracted FieldData objects
        """
        fields = []
        
        if not (hasattr(analyze_result, 'documents') and analyze_result.documents):
            return fields
        
        for document in analyze_result.documents:
            if not (hasattr(document, 'fields') and document.fields):
                continue
            
            for field_name, field_value in document.fields.items():
                normalized_field_name = FieldExtractor.normalize_field_name(field_name)
                matched_field = FieldExtractor.match_expected_field(
                    normalized_field_name,
                    expected_fields
                )
                
                field_name_to_use = matched_field if matched_field else field_name
                field_data = FieldExtractor.extract_field_data(field_name_to_use, field_value)
                
                if field_data:
                    fields.append(field_data)
                    found_fields.add(field_name_to_use)
        
        return fields
    
    @staticmethod
    def extract_from_key_value_pairs(
        analyze_result: Any,
        expected_fields: Set[str],
        found_fields: Set[str]
    ) -> List[FieldData]:
        """
        Extract fields from key-value pairs.
        
        Args:
            analyze_result: Result from Azure Document Intelligence
            expected_fields: Set of expected field names
            found_fields: Set to track found fields
            
        Returns:
            List of extracted FieldData objects
        """
        fields = []
        
        if not (hasattr(analyze_result, 'key_value_pairs') and analyze_result.key_value_pairs):
            return fields
        
        for kv_pair in analyze_result.key_value_pairs:
            # Get key content
            key_content = ""
            if hasattr(kv_pair, 'key') and kv_pair.key:
                if hasattr(kv_pair.key, 'content'):
                    key_content = str(kv_pair.key.content).strip()
                elif hasattr(kv_pair.key, 'text'):
                    key_content = str(kv_pair.key.text).strip()
            
            # Get value content
            value_content = ""
            if hasattr(kv_pair, 'value') and kv_pair.value:
                if hasattr(kv_pair.value, 'content'):
                    value_content = str(kv_pair.value.content).strip()
                elif hasattr(kv_pair.value, 'text'):
                    value_content = str(kv_pair.value.text).strip()
            
            # Get confidence
            confidence = None
            if hasattr(kv_pair, 'confidence') and kv_pair.confidence is not None:
                confidence = round(kv_pair.confidence * 100, 2)
            
            # Match with expected fields
            normalized_key = FieldExtractor.normalize_field_name(key_content)
            matched_field = FieldExtractor.match_expected_field(normalized_key, expected_fields)
            
            field_name_to_use = matched_field if matched_field else key_content
            
            # Add if not already found
            if key_content and field_name_to_use not in found_fields:
                fields.append(FieldData(
                    field_name=field_name_to_use,
                    field_value=value_content if value_content else EMPTY,
                    confidence=confidence
                ))
                found_fields.add(field_name_to_use)
        
        return fields
    
    @staticmethod
    def extract_fields(analyze_result: Any) -> List[FieldData]:
        """
        Extract field information from Azure Document Intelligence result.
        
        Args:
            analyze_result: Result from Azure Document Intelligence analyze operation
            
        Returns:
            List of FieldData objects containing field information
        """
        expected_fields_set = set(EXPECTED_FIELDS)
        found_fields: Set[str] = set()
        fields: List[FieldData] = []
        
        # Extract from structured documents first
        fields.extend(
            FieldExtractor.extract_from_structured_documents(
                analyze_result,
                expected_fields_set,
                found_fields
            )
        )
        
        # Extract from key-value pairs
        fields.extend(
            FieldExtractor.extract_from_key_value_pairs(
                analyze_result,
                expected_fields_set,
                found_fields
            )
        )
        
        # Ensure all expected fields are present (even if empty)
        for expected_field in expected_fields_set:
            if expected_field not in found_fields:
                fields.append(FieldData(
                    field_name=expected_field,
                    field_value=NOT_FOUND,
                    confidence=None
                ))
        
        # Sort fields: expected fields first, then others
        def sort_key(field: FieldData) -> tuple[int, int]:
            if field.field_name in expected_fields_set:
                return (0, EXPECTED_FIELDS.index(field.field_name))
            return (1, 0)
        
        fields.sort(key=sort_key)
        
        return fields

