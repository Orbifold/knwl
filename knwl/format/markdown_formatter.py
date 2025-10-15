"""
Markdown formatter for Knwl models.

This module provides Markdown output for Knwl models, useful for
documentation, reports, and integration with static site generators.
"""

from typing import Any, Dict, List
from pydantic import BaseModel

from knwl.format.formatter_base import FormatterBase, ModelFormatter, get_registry


class MarkdownFormatter(FormatterBase):
    """
    Formatter for Markdown output.
    
    Creates GitHub-flavored Markdown with tables and code blocks.
    """
    
    def __init__(self):
        """Initialize the Markdown formatter."""
        self._registry = get_registry()
        self._indent_level = 0
    
    def format(self, obj: Any, **options) -> str:
        """
        Format an object as Markdown.
        
        Args:
            obj: The object to format
            **options: Formatting options
            
        Returns:
            Markdown string
        """
        if obj is None:
            return "_None_"
        
        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            formatter_class = self._registry.get_formatter(type(obj), "markdown")
            if formatter_class:
                formatter = formatter_class()
                return formatter.format(obj, self, **options)
            else:
                return self._format_default_model(obj, **options)
        
        # Handle lists
        if isinstance(obj, list):
            return self._format_list(obj, **options)
        
        # Handle dicts
        if isinstance(obj, dict):
            return self._format_dict(obj, **options)
        
        # Handle primitives
        return self._format_primitive(obj)
    
    def render(self, obj: Any, **options) -> None:
        """
        Render Markdown to stdout (or save to file if specified).
        
        Args:
            obj: The object to render
            **options: Rendering options (can include 'output_file')
        """
        md_output = self.format(obj, **options)
        
        # Add frontmatter if requested
        if options.get("add_frontmatter", False):
            title = options.get("title", "Knwl Output")
            md_output = self._add_frontmatter(md_output, title)
        
        output_file = options.get("output_file")
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_output)
        else:
            print(md_output)
    
    def _format_default_model(self, model: BaseModel, **options) -> str:
        """Format a Pydantic model with default Markdown styling."""
        title = options.get("title", model.__class__.__name__)
        level = options.get("level", 2)
        
        lines = []
        lines.append(f"{'#' * level} {title}\n")
        
        # Create table
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        
        for field_name, field_value in model.model_dump().items():
            value_str = self._format_value_for_table(field_value)
            lines.append(f"| **{field_name}** | {value_str} |")
        
        return "\n".join(lines)
    
    def _format_list(self, items: List, **options) -> str:
        """Format a list as Markdown."""
        if not items:
            return "_Empty list_"
        
        lines = []
        for item in items:
            if isinstance(item, BaseModel):
                # For models, create a sub-section
                item_md = self.format(item, level=options.get("level", 2) + 1)
                lines.append(f"- {item_md}")
            else:
                lines.append(f"- {self._escape(str(item))}")
        
        return "\n".join(lines)
    
    def _format_dict(self, data: Dict, **options) -> str:
        """Format a dictionary as Markdown table."""
        if not data:
            return "_Empty dictionary_"
        
        lines = []
        lines.append("| Key | Value |")
        lines.append("|-----|-------|")
        
        for key, value in data.items():
            value_str = self._format_value_for_table(value)
            lines.append(f"| `{self._escape(str(key))}` | {value_str} |")
        
        return "\n".join(lines)
    
    def _format_primitive(self, value: Any) -> str:
        """Format primitive values as Markdown."""
        if isinstance(value, bool):
            return f"**{value}**" if value else f"_{value}_"
        elif isinstance(value, (int, float)):
            return f"`{value}`"
        elif isinstance(value, str):
            return self._escape(value)
        else:
            return self._escape(str(value))
    
    def _format_value_for_table(self, value: Any) -> str:
        """Format a value for display in a Markdown table cell."""
        if value is None:
            return "_None_"
        elif isinstance(value, bool):
            return f"**{value}**" if value else f"_{value}_"
        elif isinstance(value, list):
            return f"_[{len(value)} items]_"
        elif isinstance(value, dict):
            return f"_{{{len(value)} keys}}_"
        elif isinstance(value, BaseModel):
            return f"`{value.__class__.__name__}`"
        else:
            str_value = str(value)
            if len(str_value) > 80:
                str_value = str_value[:80] + "..."
            return self._escape(str_value)
    
    def _escape(self, text: str) -> str:
        """Escape special Markdown characters."""
        # Escape pipe characters for tables
        text = text.replace("|", "\\|")
        return text
    
    def _add_frontmatter(self, content: str, title: str) -> str:
        """Add YAML frontmatter to the Markdown."""
        from datetime import datetime
        
        frontmatter = f"""---
title: {title}
date: {datetime.now().isoformat()}
generator: Knwl Framework
---

"""
        return frontmatter + content
    
    def create_heading(self, text: str, level: int = 2) -> str:
        """Create a Markdown heading."""
        return f"{'#' * level} {text}\n"
    
    def create_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Create a Markdown table."""
        lines = []
        
        # Header
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Rows
        for row in rows:
            lines.append("| " + " | ".join([self._escape(str(cell)) for cell in row]) + " |")
        
        return "\n".join(lines)
    
    def create_code_block(self, code: str, language: str = "") -> str:
        """Create a Markdown code block."""
        return f"```{language}\n{code}\n```"
