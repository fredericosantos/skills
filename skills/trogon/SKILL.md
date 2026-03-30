---
name: trogon
description: "Guide for integrating Trogon auto-TUI into Click and Typer CLI applications, and customizing the generated terminal UI with custom widgets, theming, and parameter controls. Use this skill whenever the user mentions Trogon, wants to add a TUI to a CLI app, asks about auto-generating terminal interfaces for command-line tools, wants to customize a Trogon-generated UI, or is working with Click/Typer apps and mentions interactive forms, terminal UIs, or command builders. Also trigger when the user mentions 'tui decorator', 'init_tui', or references the trogon package."
---

# Trogon: Auto-TUI for Click & Typer CLIs

Trogon automatically generates interactive terminal user interfaces from Click and Typer CLI applications. It introspects a CLI's command structure — options, arguments, subcommands, types, defaults — and renders a form-based Textual TUI where users can fill in parameters and execute commands visually.

Think of it as "Swagger for CLIs": it solves the discoverability problem of command-line tools by giving them a visual, interactive interface with zero manual UI code.

## Quick Integration

### Click Apps

Two lines of code. The `@tui()` decorator adds a `tui` subcommand that launches the interactive interface.

```python
from trogon import tui

@tui()
@click.group()
def cli():
    """My awesome CLI tool."""
    pass
```

For single commands (not groups), Trogon wraps the command in a group automatically:

```python
@tui()
@click.command()
@click.option("--name", help="Your name")
def hello(name):
    click.echo(f"Hello {name}")
```

The `@tui()` decorator accepts these parameters:
- `name` — App name shown in the TUI header (auto-detected if not set)
- `command` — Name of the TUI subcommand (default: `"tui"`)
- `help` — Help text for the TUI subcommand (default: `"Open Textual TUI."`)

**Decorator order matters:** `@tui()` must be the outermost decorator (above `@click.group()` or `@click.command()`).

### Typer Apps

```python
import typer
from trogon.typer import init_tui

app = typer.Typer()
init_tui(app)

@app.command()
def hello(name: str):
    print(f"Hello {name}")
```

`init_tui(app, name=None)` registers a `tui` subcommand on the Typer app. The optional `name` parameter sets the app name displayed in the TUI header.

**Requires the typer extra:** `pip install trogon[typer]`

## How Trogon Works Internally

Understanding the pipeline helps when customizing or debugging:

1. **Introspection** (`trogon/introspect.py`): `introspect_click_app()` recursively walks the Click command tree, producing a hierarchy of `CommandSchema` dataclasses. Each schema contains `OptionSchema` and `ArgumentSchema` entries with type info, defaults, choices, help text, and flags.

2. **UI Rendering** (`trogon/trogon.py`): The `Trogon` app (a Textual `App`) launches a `CommandBuilder` screen. This screen has three main areas:
   - **Sidebar** — `CommandTree` widget showing the command hierarchy (hidden for single commands)
   - **Form body** — `CommandForm` widget that dynamically generates input controls based on the selected command's schema
   - **Preview bar** — Shows the CLI command string that will be executed

3. **Type-to-Widget Mapping** (`trogon/widgets/parameter_controls.py`): `ParameterControls.get_control_method()` maps Click parameter types to Textual widgets:
   - `STRING`, `INT`, `FLOAT`, `UUID`, `Path`, `File`, `IntRange`, `FloatRange` → `Input` (text field)
   - `BOOL` → `Checkbox`
   - `Choice` → `Select` (dropdown), or `MultipleChoice` if `multiple=True`
   - `Tuple` → Multiple `Input` widgets (one per element)
   - Unknown types → Falls back to `Input`

4. **Execution** (`trogon/run_command.py`): When the user presses Ctrl+R, `UserCommandData.to_cli_args()` serializes form values back to CLI arguments. The app exits and uses `os.execvp()` to run the assembled command.

## Customizing the TUI

### Theming with SCSS

Trogon uses Textual's SCSS-based styling. The default styles live in `trogon/trogon.scss`. Override them in your own Textual app by subclassing `Trogon` or `CommandBuilder`:

```python
from trogon.trogon import Trogon, CommandBuilder

class MyTrogon(Trogon):
    CSS = """
    /* Override sidebar background */
    #home-sidebar {
        background: $surface;
    }

    /* Style the command preview bar */
    #home-exec-preview {
        background: $primary-darken-1;
    }

    /* Customize the command tree */
    CommandTree {
        background: $surface;
        width: 30;
    }

    CommandTree:focus {
        border: tall $accent;
    }
    """
```

Key CSS IDs and classes you can target:
- `#home-sidebar` — Left sidebar containing the command tree
- `#home-body` — Main content area
- `#home-body-scroll` — Scrollable form container
- `#home-exec-preview` — Bottom command preview bar
- `#home-exec-preview-static` — The actual command text
- `#home-command-description` — Command description header
- `#home-command-description-container` — Description header container
- `CommandTree` — The command tree widget
- `CommandForm` — The form container
- `ParameterControls` — Individual parameter control groups
- `ControlGroup` — Groups of related input widgets
- `.command-form-input` — Text input fields
- `.command-form-checkbox` — Checkbox controls
- `.command-form-select` — Dropdown selects
- `.command-form-multiple-choice` — Multi-select widgets
- `.command-form-label` — Parameter labels
- `.command-form-control-help-text` — Help text below controls
- `.add-another-button` — The "+ value" button for multi-value params

Component classes on `CommandBuilder` (for Rich text styling):
- `version-string` — App version in the sidebar header
- `prompt` — The `$` prompt in the preview bar
- `command-name-syntax` — The app name in the preview bar

### Adding Custom Parameter Widgets

To handle a custom Click type with a specialized widget, subclass `ParameterControls` and override `get_control_method()`:

```python
from trogon.widgets.parameter_controls import ParameterControls, ControlWidgetType

class MyParameterControls(ParameterControls):
    def get_control_method(self, argument_type):
        if isinstance(argument_type, MyCustomType):
            return self.make_my_custom_control
        return super().get_control_method(argument_type)

    @staticmethod
    def make_my_custom_control(default, label, multiple, schema, control_id):
        # Return an iterable of Textual widgets
        widget = Input(
            placeholder="Enter value...",
            classes=f"command-form-input {control_id}",
        )
        yield widget
```

Then wire it into the form by subclassing `CommandForm` to use your custom `ParameterControls`.

### Subclassing the Trogon App

For deeper customization, subclass `Trogon` and/or `CommandBuilder`:

```python
from trogon.trogon import Trogon, CommandBuilder

class MyCommandBuilder(CommandBuilder):
    BINDINGS = [
        *CommandBuilder.BINDINGS,
        Binding(key="ctrl+h", action="custom_help", description="Custom Help"),
    ]

    def action_custom_help(self):
        # Your custom action
        pass

class MyTrogon(Trogon):
    def get_default_screen(self):
        return MyCommandBuilder(self.cli, self.app_name, self.command_name)
```

### Key Bindings

Default bindings (defined on `CommandBuilder`):
- **Ctrl+R** — Close & Run the command
- **Ctrl+T** — Focus command tree
- **Ctrl+O** — Show command info panel
- **Ctrl+S** — Focus search/filter input
- **F1** — About dialog

## Supported Click/Typer Features

**Fully supported:**
- Boolean flags (`--flag/--no-flag`), counting flags (`-vvv`)
- Options with `multiple=True` (repeatable)
- Arguments (positional)
- `click.Choice` with dropdown or multi-select
- `nargs=N` and `nargs=-1` (variadic arguments)
- `click.Tuple` (compound types)
- Nested subcommand groups
- Default values
- Help text on options
- `click.IntRange` / `click.FloatRange` (rendered with min/max labels)

**Limitations to be aware of:**
- Custom `click.ParamType` subclasses get a plain text input (no specialized widget)
- Parameter callbacks and validators are not executed in the TUI
- `click.File` shows a text input, not a file picker
- Mutually exclusive option groups are not enforced
- Hidden commands/options are still displayed
- Dynamic defaults (from callbacks) show as static

## Common Patterns

### Adding Trogon to an existing Click app

1. Install: `pip install trogon`
2. Add `from trogon import tui`
3. Add `@tui()` as the **outermost** decorator on your group/command
4. Run: `mycli tui`

### Adding Trogon to an existing Typer app

1. Install: `pip install trogon[typer]`
2. Add `from trogon.typer import init_tui`
3. Call `init_tui(app)` after creating the Typer app
4. Run: `mycli tui`

### Customizing the TUI command name

```python
# Click
@tui(command="ui", help="Launch interactive mode")

# Typer — not directly configurable via init_tui,
# but you can modify the app command after init
```

### Running the examples

```bash
cd /home/fsx/repos/trogon
python examples/demo.py tui        # Click group example
python examples/typer.py tui       # Typer example
python examples/nogroup_demo.py tui # Single command example
```
