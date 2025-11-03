"""
HTML formatter for Knwl models.

This module provides HTML output for Knwl models, useful for
web-based displays, documentation, and reports.
"""

from typing import Any, Dict, List
from pydantic import BaseModel
import html

from knwl.format.formatter_base import FormatterBase, ModelFormatter, get_registry


class HTMLFormatter(FormatterBase):
    """
    Formatter for HTML output.
    
    Creates semantic HTML with CSS classes for styling.
    """
    
    def __init__(self, css_classes: Dict[str, str] = None):
        """
        Initialize the HTML formatter.
        
        Args:
            css_classes: Optional custom CSS class mappings
        """
        self.css_classes = css_classes or {
            "container": "knwl-container",
            "panel": "knwl-panel",
            "title": "knwl-title",
            "subtitle": "knwl-subtitle",
            "table": "knwl-table",
            "key": "knwl-key",
            "value": "knwl-value",
            "list": "knwl-list",
            "code": "knwl-code",
        }
        self._registry = get_registry()
    
    def format(self, obj: Any, **options) -> str:
        """
        Format an object as HTML.
        
        Args:
            obj: The object to format
            **options: Formatting options
            
        Returns:
            HTML string
        """
        if obj is None:
            return '<span class="knwl-null">None</span>'
        
        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            formatter_class = self._registry.get_formatter(type(obj), "html")
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
        Render HTML to stdout (or save to file if specified).
        
        Args:
            obj: The object to render
            **options: Rendering options (can include 'output_file')
        """
        html_output = self.format(obj, **options)
        
        # Add basic HTML structure if requested
        if options.get("full_page", False):
            html_output = self._wrap_in_page(html_output, options.get("title", "Knwl Output"))
        
        output_file = options.get("output_file")
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_output)
        else:
            print(html_output)
    
    def _format_default_model(self, model: BaseModel, **options) -> str:
        """Format a Pydantic model with default HTML styling."""
        title = options.get("title", model.__class__.__name__)
        
        rows = []
        for field_name, field_value in model.model_dump().items():
            key_html = f'<td class="{self.css_classes["key"]}">{html.escape(field_name)}</td>'
            value_html = f'<td class="{self.css_classes["value"]}">{self._format_value(field_value)}</td>'
            rows.append(f"<tr>{key_html}{value_html}</tr>")
        
        table_html = f'''
        <table class="{self.css_classes['table']}">
            {''.join(rows)}
        </table>
        '''
        
        return f'''
        <div class="{self.css_classes['panel']}">
            <h3 class="{self.css_classes['title']}">{html.escape(title)}</h3>
            {table_html}
        </div>
        '''
    
    def _format_list(self, items: List, **options) -> str:
        """Format a list as HTML."""
        if not items:
            return '<span class="knwl-empty">[]</span>'
        
        list_items = []
        for item in items:
            if isinstance(item, BaseModel):
                list_items.append(f"<li>{self.format(item, **options)}</li>")
            else:
                list_items.append(f"<li>{html.escape(str(item))}</li>")
        
        return f'<ul class="{self.css_classes["list"]}">{"".join(list_items)}</ul>'
    
    def _format_dict(self, data: Dict, **options) -> str:
        """Format a dictionary as HTML table."""
        rows = []
        for key, value in data.items():
            key_html = f'<td class="{self.css_classes["key"]}">{html.escape(str(key))}</td>'
            value_html = f'<td class="{self.css_classes["value"]}">{self._format_value(value)}</td>'
            rows.append(f"<tr>{key_html}{value_html}</tr>")
        
        return f'<table class="{self.css_classes["table"]}">{"".join(rows)}</table>'
    
    def _format_primitive(self, value: Any) -> str:
        """Format primitive values as HTML."""
        if isinstance(value, bool):
            css_class = "knwl-bool-true" if value else "knwl-bool-false"
            return f'<span class="{css_class}">{value}</span>'
        elif isinstance(value, (int, float)):
            return f'<span class="knwl-number">{value}</span>'
        elif isinstance(value, str):
            return html.escape(value)
        else:
            return html.escape(str(value))
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display in HTML."""
        if value is None:
            return '<span class="knwl-null">None</span>'
        elif isinstance(value, bool):
            css_class = "knwl-bool-true" if value else "knwl-bool-false"
            return f'<span class="{css_class}">{value}</span>'
        elif isinstance(value, list):
            return f'<span class="knwl-count">[{len(value)} items]</span>'
        elif isinstance(value, dict):
            return f'<span class="knwl-count">{{{len(value)} keys}}</span>'
        elif isinstance(value, BaseModel):
            return f'<span class="knwl-type">{value.__class__.__name__}</span>'
        else:
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:100] + "..."
            return html.escape(str_value)
    
    def _wrap_in_page(self, content: str, title: str) -> str:
        """Wrap content in a full HTML page with basic styling."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .{self.css_classes['container']} {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .{self.css_classes['panel']} {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 16px;
            margin: 16px 0;
        }}
        .{self.css_classes['title']} {{
            color: #2196F3;
            margin-top: 0;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 8px;
        }}
        .{self.css_classes['subtitle']} {{
            color: #666;
            font-size: 0.9em;
            margin-top: -8px;
            margin-bottom: 16px;
        }}
        .{self.css_classes['table']} {{
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0;
        }}
        .{self.css_classes['table']} td {{
            padding: 8px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .{self.css_classes['key']} {{
            font-weight: bold;
            color: #FF9800;
            width: 200px;
        }}
        .{self.css_classes['value']} {{
            color: #333;
        }}
        .{self.css_classes['list']} {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        .knwl-number {{
            color: #9C27B0;
            font-weight: bold;
        }}
        .knwl-bool-true {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .knwl-bool-false {{
            color: #F44336;
            font-weight: bold;
        }}
        .knwl-null {{
            color: #999;
            font-style: italic;
        }}
        .knwl-type {{
            color: #4CAF50;
            font-style: italic;
        }}
        .knwl-count {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="{self.css_classes['container']}">
        {content}
    </div>
</body>
</html>'''
