"""
Rich terminal formatter for Knwl models.

This module provides a beautiful terminal output using the Rich library,
with consistent styling and formatting across all Knwl models.
"""

import json
from typing import Any, Optional, List, Dict
from pydantic import BaseModel

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich import box

from knwl.format.formatter_base import FormatterBase, ModelFormatter, get_registry


class RichTheme:
    """Centralized theme configuration for consistent styling."""

    # Colors
    PRIMARY = "cyan"
    SECONDARY = "blue"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    MUTED = "dim"
    HIGHLIGHT = "magenta"

    # Styles
    TITLE_STYLE = "bold cyan"
    SUBTITLE_STYLE = "bold blue"
    KEY_STYLE = "bold yellow"
    VALUE_STYLE = "white"
    TYPE_STYLE = "italic green"
    ID_STYLE = "dim cyan"

    # Box styles
    PANEL_BOX = box.ROUNDED
    TABLE_BOX = box.SIMPLE

    # Borders
    BORDER_STYLE = "cyan"


class RichFormatter(FormatterBase):
    """
    Formatter for rich terminal output.

    This formatter uses the Rich library to create beautiful,
    colorful terminal output with tables, panels, and trees.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the Rich formatter.

        Args:
            console: Optional Rich Console instance. If not provided, creates a new one.
        """
        self.console = console or Console(width=80)
        self.theme = RichTheme()
        self._registry = get_registry()

    def format(self, obj: Any, **options) -> Any:
        """
        Format an object using Rich components.

        Args:
            obj: The object to format
            **options: Formatting options

        Returns:
            Rich renderable object (Panel, Table, Tree, etc.)
        """
        # Handle None
        if obj is None:
            return Text("None", style=self.theme.MUTED)
        if isinstance(obj, str):
            if obj.strip().startswith("@/"):
                from knwl.config import resolve_config

                return json.dumps(resolve_config(obj.strip()), indent=2)
            elif obj.strip().startswith("$/"):
                from knwl.utils import get_full_path

                path = get_full_path(obj.strip())
                return path
            else:
                return f"To render a configuration, use the '@/service/variant' syntax. For example, `@/vector/memory', '@/llm/openai' or simply '@/' for the whole config."
        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            formatter_class = self._registry.get_formatter(type(obj), "terminal")
            if formatter_class:
                formatter = formatter_class()
                return formatter.format(obj, self, **options)
            else:
                # Fall back to default Pydantic formatting
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
        Render an object to the console.

        Args:
            obj: The object to render
            **options: Rendering options
        """
        formatted = self.format(obj, **options)
        self.console.print(formatted)

    def _format_default_model(self, model: BaseModel, **options) -> Panel:
        """Format a Pydantic model with default styling."""
        title = options.get("title", model.__class__.__name__)

        table = Table(
            show_header=False, box=self.theme.TABLE_BOX, padding=(0, 1), expand=True
        )
        table.add_column("Field", style=self.theme.KEY_STYLE)
        table.add_column("Value", style=self.theme.VALUE_STYLE)

        for field_name, field_value in model.model_dump().items():
            value_str = self._format_value_for_table(field_value)
            table.add_row(field_name, value_str)

        return Panel(
            table,
            title=f"[{self.theme.TITLE_STYLE}]{title}[/{self.theme.TITLE_STYLE}]",
            border_style=self.theme.BORDER_STYLE,
            box=self.theme.PANEL_BOX,
        )

    def _format_list(self, items: List, **options) -> Any:
        """Format a list of items."""
        if not items:
            return Text("[]", style=self.theme.MUTED)

        # If all items are models, create a compact representation
        if all(isinstance(item, BaseModel) for item in items):
            return self._format_model_list(items, **options)

        # Otherwise, format as bullet list
        lines = []
        for item in items:
            lines.append(f"• {item}")
        return "\n".join(lines)

    def _format_model_list(self, models: list[BaseModel], **options) -> Table:
        """Format a list of Pydantic models as a table."""
        if not models:
            return Text("No items", style=self.theme.MUTED)

        model_type = type(models[0])
        fields = list(models[0].model_fields.keys())

        # Limit fields if too many
        max_fields = options.get("max_fields", 5)
        if len(fields) > max_fields:
            fields = fields[:max_fields]

        table = Table(
            box=self.theme.TABLE_BOX,
            show_header=True,
            header_style=self.theme.SUBTITLE_STYLE,
        )

        for field in fields:
            table.add_column(field.replace("_", " ").title())

        for model in models:
            values = []
            for field in fields:
                value = getattr(model, field, None)
                values.append(self._format_value_for_table(value))
            table.add_row(*values)

        return table

    def _format_dict(self, data: Dict, **options) -> Table:
        """Format a dictionary as a table."""
        table = Table(show_header=False, box=self.theme.TABLE_BOX, padding=(0, 1))
        table.add_column("Key", style=self.theme.KEY_STYLE)
        table.add_column("Value", style=self.theme.VALUE_STYLE)

        for key, value in data.items():
            value_str = self._format_value_for_table(value)
            table.add_row(str(key), value_str)

        return table

    def _format_primitive(self, value: Any) -> Text:
        """Format primitive values."""
        if isinstance(value, bool):
            return Text(
                str(value), style=self.theme.SUCCESS if value else self.theme.ERROR
            )
        elif isinstance(value, (int, float)):
            return Text(str(value), style=self.theme.HIGHLIGHT)
        elif isinstance(value, str):
            return Text(value, style=self.theme.VALUE_STYLE)
        else:
            return Text(str(value), style=self.theme.MUTED)

    def _format_value_for_table(self, value: Any, max_length: int = 150) -> str:
        """Format a value for display in a table cell."""
        if value is None:
            return "[dim]None[/dim]"
        elif isinstance(value, bool):
            style = self.theme.SUCCESS if value else self.theme.ERROR
            return f"[{style}]{value}[/{style}]"
        elif isinstance(value, list):
            if len(value) == 0:
                return "[dim][][/dim]"
            elif len(value) <= 3:
                return f"[{self.theme.MUTED}][{len(value)} items][/{self.theme.MUTED}]"
            else:
                return f"[{self.theme.MUTED}][{len(value)} items][/{self.theme.MUTED}]"
        elif isinstance(value, dict):
            return f"[{self.theme.MUTED}]{{{len(value)} keys}}[/{self.theme.MUTED}]"
        elif isinstance(value, BaseModel):
            return f"[{self.theme.TYPE_STYLE}]{value.__class__.__name__}[/{self.theme.TYPE_STYLE}]"
        else:
            str_value = str(value)
            if len(str_value) > max_length:
                str_value = str_value[: max_length - 3] + "..."
            return str_value

    def create_panel(
        self, content: Any, title: str, subtitle: Optional[str] = None, **kwargs
    ) -> Panel:
        """
        Create a styled panel.

        Args:
            content: The content to display in the panel
            title: Panel title
            subtitle: Optional subtitle
            **kwargs: Additional panel options
        """
        return Panel(
            content,
            title=f"[{self.theme.TITLE_STYLE}]{title}[/{self.theme.TITLE_STYLE}]",
            subtitle=(
                f"[{self.theme.MUTED}]{subtitle}[/{self.theme.MUTED}]"
                if subtitle
                else None
            ),
            border_style=kwargs.get("border_style", self.theme.BORDER_STYLE),
            box=kwargs.get("box", self.theme.PANEL_BOX),
            **{k: v for k, v in kwargs.items() if k not in ["border_style", "box"]},
        )

    def create_table(
        self, title: Optional[str] = None, columns: Optional[list[str]] = None, **kwargs
    ) -> Table:
        """
        Create a styled table.

        Args:
            title: Optional table title
            columns: List of column names
            **kwargs: Additional table options
        """
        table = Table(
            title=(
                f"[{self.theme.SUBTITLE_STYLE}]{title}[/{self.theme.SUBTITLE_STYLE}]"
                if title
                else None
            ),
            box=kwargs.get("box", self.theme.TABLE_BOX),
            show_header=kwargs.get("show_header", True),
            header_style=kwargs.get("header_style", self.theme.SUBTITLE_STYLE),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["box", "show_header", "header_style"]
            },
        )

        if columns:
            for col in columns:
                table.add_column(col)

        return table

    def create_tree(self, label: str, **kwargs) -> Tree:
        """
        Create a styled tree.

        Args:
            label: Root label
            **kwargs: Additional tree options
        """
        return Tree(
            f"[{self.theme.TITLE_STYLE}]{label}[/{self.theme.TITLE_STYLE}]", **kwargs
        )
