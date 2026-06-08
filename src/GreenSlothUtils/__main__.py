from collections.abc import Iterable
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalScroll,
)
from textual.validation import Regex
from textual.widgets import (
    Button,
    ContentSwitcher,
    Digits,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
)

from GreenSlothUtils import installerfuncs


class ModelPathSelection(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if not path.name.startswith(".")]
class GreenSlothInitialize(App):
    """A Textual app to manage stopwatches."""
    
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        ("s", "starting_page", "Show Starting Page")
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        with ContentSwitcher(initial="start-page"):
            with Vertical(id="start-page"):
                yield Button("Create New Model", id="button-switchpage-createmodel")
                yield Button("Edit Existing Model", id="button-switchpage-editmodel")
                yield Button("Step-By-Step Guide", id="button-stepguide")
                
            with Vertical(id="create-model-page"):
                yield HorizontalGroup(
                    Label("Please select a directory", id="directory-label"),
                    Input(
                        placeholder="Enter Model Name. Must be like Corvest2000",
                        validators=[Regex(r"^[A-Z][a-zA-Z]*[0-9]{4}$")],
                        restrict=r"[a-zA-Z0-9]*",
                        id="input-modelname"
                    ),
                    Button("Create", id="button-modelcreate", variant="default", disabled=True),
                    id="create-model-firstrow"
                )
                yield ModelPathSelection("./", id="create-model-directory")
                
            with Vertical(id="editmodel-select-page"):
                yield HorizontalGroup(
                    Label("Please select a Model directory", id="directory-select-label"),
                    Button("Select", id="button-modelselect", variant="default", disabled=True),
                )
                yield ModelPathSelection("./", id="create-model-directory")


    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
        
    def action_quit(self) -> None:
        self.exit()
        
    def action_starting_page(self) -> None:
        switcher = self.query_one(ContentSwitcher)
        switcher.current = "start-page"

    #### Buttons
    
    @on(Button.Pressed, "#button-switchpage-createmodel")
    def switch_to_create_model(self) -> None:
        switcher = self.query_one(ContentSwitcher)
        switcher.current = "create-model-page"

    @on(Button.Pressed, "#button-switchpage-editmodel")
    def switch_to_edit_model(self) -> None:
        switcher = self.query_one(ContentSwitcher)
        switcher.current = "editmodel-select-page"
    
    @on(Button.Pressed, "#button-modelcreate")
    def create_model(self) -> None:
        model_name = self.query_one("#input-modelname", Input).value
        model_path = Path(self.query_one("#directory-label", Label).content)
        create_button = self.query_one("#button-modelcreate", Button)
        directory_tree = self.query_one("#create-model-directory", ModelPathSelection)
        
        # Add logic to create the model
        if not Path.is_dir(model_path):
            # Handle the case where the selected path is not a directory
            create_button.variant = "error"
            create_button.label = "Invalid Directory"
        elif Path.exists(model_path / model_name):
            create_button.variant = "error"
            create_button.label = "Model Already Exists"
        elif Path.exists(model_path / "model_info"):
            create_button.variant = "error"
            create_button.label = "Selected Directory Already a Model"
        else:
            create_button.variant = "success"
            create_button.label = "Create"
            installerfuncs.gs_install(model_name, Path(model_path))
            directory_tree.reload()

    ### Input Events
    
    @on(Input.Changed, "#input-modelname")
    def check_modelname(self) -> None:
        input_modelname = self.query_one("#input-modelname", Input)
        create_button = self.query_one("#button-modelcreate", Button)
        create_button.label = "Create"
        if input_modelname.is_valid:
            input_modelname.add_class("valid")
            input_modelname.remove_class("invalid")
            create_button.disabled = False
            create_button.variant = "success"
        else:
            input_modelname.add_class("invalid")
            input_modelname.remove_class("valid")
            create_button.disabled = True
            create_button.variant = "default"

    ### Directory Tree Events
    
    @on(DirectoryTree.DirectorySelected, "#create-model-directory")
    def update_directory_label(self, event: DirectoryTree.DirectorySelected) -> None:
        """Update the directory label with the selected path."""
        self.query_one("#directory-label", Label).update(str(event.path) + "/")

if __name__ == "__main__":
    app = GreenSlothInitialize()
    app.run()