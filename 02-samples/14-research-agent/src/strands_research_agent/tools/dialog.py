"""Interactive Dialog Tool for Strands

This tool provides advanced dialog interfaces for interactive user communication,
including form validation, rich text, password input, multi-field forms,
file selection, progress bars, and more.
"""

import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from prompt_toolkit import prompt
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.completion import PathCompleter, WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.layout import D, HSplit, Layout
from prompt_toolkit.shortcuts import (
    ProgressBar,
    button_dialog,
    checkboxlist_dialog,
    input_dialog,
    message_dialog,
    radiolist_dialog,
    yes_no_dialog,
)
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from prompt_toolkit.widgets import Button, Dialog, Label, TextArea
from strands import tool

# Define some preset styles
STYLE_PRESETS = {
    "default": {
        "dialog": "bg:#f0f0f0",
        "dialog frame.label": "bg:#6688ff #ffffff",
        "dialog.body": "bg:#ffffff #000000",
        "dialog shadow": "bg:#222222",
        "button.focused": "bg:#6688ff #ffffff",
        "text-area.cursor": "#000000",
        "text-area": "bg:#ffffff #000000",
    },
    "blue": {
        "dialog": "bg:#4444ff",
        "dialog frame.label": "bg:#6688ff #ffffff",
        "dialog.body": "bg:#ffffff #000000",
        "dialog shadow": "bg:#222288",
        "button.focused": "bg:#6688ff #ffffff",
        "text-area.cursor": "#000000",
        "text-area": "bg:#ffffff #000000",
    },
    "green": {
        "dialog": "bg:#286c3a",
        "dialog frame.label": "bg:#44aa55 #ffffff",
        "dialog.body": "bg:#ffffff #000000",
        "dialog shadow": "bg:#222222",
        "button.focused": "bg:#44aa55 #ffffff",
        "text-area.cursor": "#000000",
        "text-area": "bg:#ffffff #000000",
    },
    "purple": {
        "dialog": "bg:#6a2c70",
        "dialog frame.label": "bg:#9a4c90 #ffffff",
        "dialog.body": "bg:#ffffff #000000",
        "dialog shadow": "bg:#222222",
        "button.focused": "bg:#9a4c90 #ffffff",
        "text-area.cursor": "#000000",
        "text-area": "bg:#ffffff #000000",
    },
    "dark": {
        "dialog": "bg:#333333",
        "dialog frame.label": "bg:#555555 #ffffff",
        "dialog.body": "bg:#222222 #ffffff",
        "dialog shadow": "bg:#111111",
        "button.focused": "bg:#555555 #ffffff",
        "text-area.cursor": "#ffffff",
        "text-area": "bg:#222222 #ffffff",
    },
}


class InputValidator(Validator):
    """Custom validator for input fields."""

    def __init__(self, validation_rules=None):
        # Convert validation_rules to dict if it's a string
        if isinstance(validation_rules, str):
            try:
                validation_rules = json.loads(validation_rules)
            except json.JSONDecodeError:
                validation_rules = {}

        self.validation_rules = validation_rules or {}
        self.error_message = self.validation_rules.get("error_message", "Invalid input")

    def validate(self, document):
        text = document.text

        # Check required
        if self.validation_rules.get("required", False) and not text.strip():
            raise ValidationError(message="This field is required")

        # Check min length
        min_length = self.validation_rules.get("min_length")
        if min_length is not None and len(text) < min_length:
            raise ValidationError(
                message=f"Input must be at least {min_length} characters"
            )

        # Check max length
        max_length = self.validation_rules.get("max_length")
        if max_length is not None and len(text) > max_length:
            raise ValidationError(
                message=f"Input must be at most {max_length} characters"
            )

        # Check pattern
        pattern = self.validation_rules.get("pattern")
        if pattern and not re.match(pattern, text):
            raise ValidationError(message=self.error_message)


async def run_message_dialog(title, text, style):
    """Run a simple message dialog."""
    await message_dialog(title=title, text=text, style=style).run_async()
    return {"acknowledged": True}


async def run_rich_message_dialog(title, text, style):
    """Run a message dialog with rich HTML formatting."""
    await message_dialog(title=title, text=HTML(text), style=style).run_async()
    return {"acknowledged": True}


async def run_input_dialog(
    title, text, default_value, style, validation=None, multiline=False
):
    """Run an input dialog with optional validation."""
    validator = InputValidator(validation) if validation else None

    if multiline:
        # Create a custom dialog with a TextArea for multiline input
        text_area = TextArea(
            text=default_value or "",
            multiline=True,
            height=D(min=3, max=10),
            line_numbers=True,
            validator=validator,
        )

        result = [None]  # Use list to capture result from dialog

        def accept_handler():
            result[0] = text_area.text
            get_app().exit(result=True)

        dialog = Dialog(
            title=title,
            body=HSplit(
                [
                    Label(text),
                    text_area,
                ]
            ),
            buttons=[
                Button(text="OK", handler=accept_handler),
                Button(text="Cancel", handler=lambda: get_app().exit(result=False)),
            ],
            with_background=True,
            style=style,
        )

        app = Application(
            layout=Layout(dialog),
            full_screen=False,
            style=style,
            mouse_support=True,
        )

        success = await app.run_async()
        return result[0] if success else None
    else:
        # Use standard input dialog for single line
        result = await input_dialog(
            title=title,
            text=text,
            default=default_value or "",
            style=style,
            validator=validator,
        ).run_async()
        return result


async def run_password_dialog(title, text, style, validation=None):
    """Run a password input dialog with masked input."""
    validator = InputValidator(validation) if validation else None

    # Create custom password dialog (prompt_toolkit's standard dialogs don't support password masking)
    password = await prompt(
        f"{text}\n", is_password=True, validator=validator, async_=True
    )

    return password


async def run_yes_no_dialog(title, text, style):
    """Run a yes/no dialog."""
    result = await yes_no_dialog(title=title, text=text, style=style).run_async()
    return result


async def run_radio_dialog(title, text, options, style):
    """Run a radio selection dialog."""
    result = await radiolist_dialog(
        title=title, text=text, values=options, style=style
    ).run_async()
    return result


async def run_checkbox_dialog(title, text, options, style):
    """Run a checkbox selection dialog."""
    result = await checkboxlist_dialog(
        title=title, text=text, values=options, style=style
    ).run_async()
    return result


async def run_button_dialog(title, text, options, style):
    """Run a button selection dialog."""
    result = await button_dialog(
        title=title,
        text=text,
        buttons=[(label, value) for value, label in options],
        style=style,
    ).run_async()
    return result


async def run_autocomplete_dialog(title, text, options, default_value, style):
    """Run an input dialog with autocomplete."""
    # Extract just the values for completion
    completion_options = [value for value, _ in options]
    completer = WordCompleter(completion_options)

    result = await prompt(
        f"{text}\n", completer=completer, default=default_value or "", async_=True
    )

    return result


async def run_file_dialog(title, text, path_filter, style):
    """Run a file selection dialog with path completion."""
    # Extract filter extension
    extension = None
    if path_filter and "*." in path_filter:
        extension = path_filter.split("*.")[1]

    # Create path completer with optional filter
    if extension:
        completer = PathCompleter(
            file_filter=lambda filename: filename.endswith(f".{extension}"),
            min_input_len=0,
        )
    else:
        completer = PathCompleter(min_input_len=0)

    # Use home directory as default starting point
    home_dir = os.path.expanduser("~")

    # Prompt with path completion
    result = await prompt(
        f"{text}\nPath: ", completer=completer, default=home_dir + "/", async_=True
    )

    # Expand user path if needed
    if result and result.startswith("~"):
        result = os.path.expanduser(result)

    return result


async def run_progress_dialog(title, text, steps, step_delay, style):
    """Run a progress bar dialog."""
    total_steps = steps or 10
    delay = step_delay or 0.1

    result = {"completed": True, "steps": total_steps}

    # Run progress bar
    with ProgressBar(title=title, formatters=[lambda progress: text]) as pb:
        for i in pb(range(total_steps)):
            await asyncio.sleep(delay)

    return result


async def run_form_dialog(title, text, fields, style):
    """Run a multi-field form dialog."""
    # Create form fields
    form_fields = []
    input_controls = {}

    # Ensure fields is properly parsed if it's a string
    if isinstance(fields, str):
        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            fields = []

    for field in fields:
        # Ensure field is a dictionary
        if not isinstance(field, dict):
            continue

        field_name = field.get("name", "")
        field_label = field.get("label", field_name)
        field_type = field.get("type", "text")
        field_default = field.get("default", "")
        field_validation = field.get("validation", {})

        # Create validator if needed
        validator = InputValidator(field_validation) if field_validation else None

        # Create appropriate input control based on type
        if field_type == "textarea":
            control = TextArea(
                text=field_default,
                multiline=True,
                height=D(min=2, max=5),
                validator=validator,
                prompt=f"{field_label}: ",
            )
        elif field_type == "password":
            control = TextArea(
                text=field_default,
                multiline=False,
                height=1,
                password=True,
                validator=validator,
                prompt=f"{field_label}: ",
            )
        elif field_type == "file":
            # For file fields, we'll add a button to browse files
            control = TextArea(
                text=field_default,
                multiline=False,
                height=1,
                validator=validator,
                prompt=f"{field_label}: ",
            )
            # File browser would need more complex logic - simplified for now
        else:  # text, number, etc.
            control = TextArea(
                text=field_default,
                multiline=False,
                height=1,
                validator=validator,
                prompt=f"{field_label}: ",
            )

        # Add label and control to form
        form_fields.append(Label(f"{field_label}:"))
        form_fields.append(control)

        # Store control for later retrieval
        input_controls[field_name] = control

    # Track form result
    form_result = [None]

    # Define handlers
    def submit_handler():
        # Collect all form values
        result = {name: control.text for name, control in input_controls.items()}
        form_result[0] = result
        get_app().exit(result=True)

    def cancel_handler():
        get_app().exit(result=False)

    # Create dialog
    dialog = Dialog(
        title=title,
        body=HSplit([Label(text)] + form_fields),
        buttons=[
            Button(text="Submit", handler=submit_handler),
            Button(text="Cancel", handler=cancel_handler),
        ],
        with_background=True,
    )
    app = Application(
        layout=Layout(dialog), full_screen=False, style=style, mouse_support=True
    )

    # Run dialog
    success = await app.run_async()

    # Return form data or None if cancelled
    return form_result[0] if success else None


async def run_dialog(
    dialog_type: str,
    title: str,
    text: str,
    options: Optional[List[Tuple[str, str]]] = None,
    style_name: str = "default",
    default_value: Optional[str] = None,
    validation: Optional[Dict] = None,
    form_fields: Optional[List[Dict]] = None,
    progress_steps: Optional[int] = None,
    step_delay: Optional[float] = None,
    key_bindings: Optional[Dict] = None,
    path_filter: Optional[str] = None,
    multiline: bool = False,
) -> Any:
    """Run the specified dialog type and return the result."""

    # Get style dictionary from presets
    style_dict = STYLE_PRESETS.get(style_name, STYLE_PRESETS["default"])

    # Convert style dictionary to Style object
    style = Style.from_dict(style_dict)

    # Run appropriate dialog type
    if dialog_type == "message":
        return await run_message_dialog(title, text, style)

    elif dialog_type == "rich_message":
        return await run_rich_message_dialog(title, text, style)

    elif dialog_type == "input":
        return await run_input_dialog(
            title, text, default_value, style, validation, multiline
        )

    elif dialog_type == "password":
        return await run_password_dialog(title, text, style, validation)

    elif dialog_type == "yes_no":
        return await run_yes_no_dialog(title, text, style)

    elif dialog_type == "radio":
        if not options:
            raise ValueError("Options are required for radio dialog")
        return await run_radio_dialog(title, text, options, style)

    elif dialog_type == "checkbox":
        if not options:
            raise ValueError("Options are required for checkbox dialog")
        return await run_checkbox_dialog(title, text, options, style)

    elif dialog_type == "buttons":
        if not options:
            raise ValueError("Options are required for buttons dialog")
        return await run_button_dialog(title, text, options, style)

    elif dialog_type == "autocomplete":
        if not options:
            raise ValueError("Options are required for autocomplete dialog")
        return await run_autocomplete_dialog(title, text, options, default_value, style)

    elif dialog_type == "file":
        return await run_file_dialog(title, text, path_filter, style)

    elif dialog_type == "progress":
        return await run_progress_dialog(title, text, progress_steps, step_delay, style)

    elif dialog_type == "form":
        if not form_fields:
            raise ValueError("Form fields are required for form dialog")
        return await run_form_dialog(title, text, form_fields, style)

    else:
        raise ValueError(f"Unknown dialog type: {dialog_type}")


@tool
def dialog(
    dialog_type: str,
    text: str,
    title: str = "Dialog",
    options: Optional[List[List[str]]] = None,
    style: str = "default",
    default_value: Optional[str] = None,
    validation: Optional[Dict[str, Any]] = None,
    form_fields: Optional[List[Dict[str, Any]]] = None,
    progress_steps: Optional[int] = None,
    step_delay: Optional[float] = None,
    key_bindings: Optional[Dict[str, str]] = None,
    path_filter: Optional[str] = None,
    multiline: bool = False,
) -> Dict[str, Any]:
    """
    Create interactive dialog interfaces with advanced features.

    Args:
        dialog_type: Type of dialog (message, input, yes_no, radio, checkbox, buttons,
                    password, progress, autocomplete, file, form, rich_message)
        text: Main text or question to display (supports HTML formatting for rich_message)
        title: Dialog title
        options: Options for radio, checkbox, buttons, or autocomplete dialogs as [value, label] pairs
        style: Dialog style theme (default, blue, green, purple, dark)
        default_value: Default value for input dialog
        validation: Validation rules for input fields with keys: pattern, min_length, max_length, required, error_message
        form_fields: Fields for multi-input form dialogs with keys: name, label, type, default, validation
        progress_steps: Number of steps for progress bar dialog
        step_delay: Delay in seconds between progress steps
        key_bindings: Custom key bindings for dialogs
        path_filter: Filter for file selection dialog (e.g., '*.py', '*.txt')
        multiline: Whether input should allow multiple lines

    Returns:
        Dictionary with dialog results and status
    """
    # Check if we're in DEV mode
    if os.environ.get("DEV", "").lower() == "true":
        return {
            "status": "success",
            "content": [
                {
                    "text": "Dialog is disabled in DEV mode. Please set DEV=false to enable interactive dialogs."
                }
            ],
        }

    try:
        # Validate style
        if style not in STYLE_PRESETS:
            style = "default"  # Fallback to default if invalid style is provided

        # Convert options to the right format if they're not already
        formatted_options = []
        if options:
            for option in options:
                if isinstance(option, list) and len(option) == 2:
                    formatted_options.append((option[0], option[1]))
                elif (
                    isinstance(option, dict) and "value" in option and "label" in option
                ):
                    formatted_options.append((option["value"], option["label"]))
                else:
                    # If format is unclear, use the option as both value and label
                    formatted_options.append((str(option), str(option)))

        # Run the dialog using asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            run_dialog(
                dialog_type=dialog_type,
                title=title,
                text=text,
                options=formatted_options,
                style_name=style,
                default_value=default_value,
                validation=validation,
                form_fields=form_fields,
                progress_steps=progress_steps,
                step_delay=step_delay,
                key_bindings=key_bindings,
                path_filter=path_filter,
                multiline=multiline,
            )
        )

        return {
            "status": "success",
            "content": [{"text": "Dialog response received:"}, {"text": str(result)}],
        }

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()

        return {
            "status": "error",
            "content": [
                {"text": f"Error displaying dialog: {str(e)}\n\n{error_details}"}
            ],
        }
