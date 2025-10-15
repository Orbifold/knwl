"""
Base classes and interfaces for the Knwl formatting system.

This module provides the foundation for a pluggable, extensible formatting system
that can render Knwl models in various output formats (terminal, HTML, markdown, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Optional, Callable
from pydantic import BaseModel


class FormatterBase(ABC):
    """
    Abstract base class for all formatters.
    
    Formatters are responsible for converting Knwl models into a specific output format.
    Each formatter should implement the format() method to handle the conversion.
    """
    
    @abstractmethod
    def format(self, obj: Any, **options) -> Any:
        """
        Format an object for output.
        
        Args:
            obj: The object to format (typically a Pydantic model)
            **options: Format-specific options
            
        Returns:
            The formatted output (type depends on formatter implementation)
        """
        pass
    
    @abstractmethod
    def render(self, obj: Any, **options) -> None:
        """
        Render an object to the output medium.
        
        Args:
            obj: The object to render
            **options: Rendering options
        """
        pass


class ModelFormatter(ABC):
    """
    Abstract base class for model-specific formatters.
    
    Each Knwl model can have its own formatter that knows how to
    best represent that model in a specific output format.
    """
    
    @abstractmethod
    def format(self, model: BaseModel, formatter: FormatterBase, **options) -> Any:
        """
        Format a specific model instance.
        
        Args:
            model: The Pydantic model instance to format
            formatter: The parent formatter being used (for context/styling)
            **options: Model-specific formatting options
            
        Returns:
            Formatted representation suitable for the parent formatter
        """
        pass


class FormatterRegistry:
    """
    Registry for mapping model types to their formatters.
    
    This allows the system to be easily extended with new models and formatters.
    The registry supports multiple output formats (terminal, html, markdown, etc.)
    """
    
    def __init__(self):
        # Structure: {formatter_type: {model_type: model_formatter}}
        self._formatters: Dict[str, Dict[Type[BaseModel], Type[ModelFormatter]]] = {}
        self._default_formatters: Dict[str, Type[ModelFormatter]] = {}
    
    def register(
        self,
        model_type: Type[BaseModel],
        formatter_class: Type[ModelFormatter],
        format_type: str = "terminal"
    ) -> None:
        """
        Register a model formatter for a specific model and output format.
        
        Args:
            model_type: The Pydantic model class
            formatter_class: The ModelFormatter class to handle this model
            format_type: The output format type (terminal, html, markdown, etc.)
        """
        if format_type not in self._formatters:
            self._formatters[format_type] = {}
        
        self._formatters[format_type][model_type] = formatter_class
    
    def register_default(
        self,
        formatter_class: Type[ModelFormatter],
        format_type: str = "terminal"
    ) -> None:
        """
        Register a default formatter for a format type.
        
        This formatter will be used for any model that doesn't have
        a specific formatter registered.
        
        Args:
            formatter_class: The default ModelFormatter class
            format_type: The output format type
        """
        self._default_formatters[format_type] = formatter_class
    
    def get_formatter(
        self,
        model_type: Type[BaseModel],
        format_type: str = "terminal"
    ) -> Optional[Type[ModelFormatter]]:
        """
        Get the formatter for a specific model and format type.
        
        Args:
            model_type: The Pydantic model class
            format_type: The output format type
            
        Returns:
            The ModelFormatter class, or None if not found
        """
        formatters = self._formatters.get(format_type, {})
        
        # Try exact match first
        if model_type in formatters:
            return formatters[model_type]
        
        # Try base classes
        for base in model_type.__mro__[1:]:
            if base in formatters:
                return formatters[base]
        
        # Fall back to default
        return self._default_formatters.get(format_type)
    
    def has_formatter(
        self,
        model_type: Type[BaseModel],
        format_type: str = "terminal"
    ) -> bool:
        """
        Check if a formatter exists for a model type.
        
        Args:
            model_type: The Pydantic model class
            format_type: The output format type
            
        Returns:
            True if a formatter is registered
        """
        return self.get_formatter(model_type, format_type) is not None


# Global registry instance
_registry = FormatterRegistry()


def register_formatter(
    model_type: Type[BaseModel],
    format_type: str = "terminal"
) -> Callable:
    """
    Decorator to register a model formatter.
    
    Usage:
        @register_formatter(KnwlNode, "terminal")
        class KnwlNodeTerminalFormatter(ModelFormatter):
            ...
    
    Args:
        model_type: The Pydantic model class
        format_type: The output format type
    """
    def decorator(formatter_class: Type[ModelFormatter]) -> Type[ModelFormatter]:
        _registry.register(model_type, formatter_class, format_type)
        return formatter_class
    return decorator


def register_default_formatter(format_type: str = "terminal") -> Callable:
    """
    Decorator to register a default formatter for a format type.
    
    Args:
        format_type: The output format type
    """
    def decorator(formatter_class: Type[ModelFormatter]) -> Type[ModelFormatter]:
        _registry.register_default(formatter_class, format_type)
        return formatter_class
    return decorator


def get_registry() -> FormatterRegistry:
    """Get the global formatter registry."""
    return _registry
