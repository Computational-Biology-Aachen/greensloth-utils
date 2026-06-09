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
    DataTable
)

from GreenSlothUtils import installerfuncs


def reset_button(button: Button, label: str, color: str) -> None:
    button.label = label
    button.variant = color

class ModelPathSelection(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if not path.name.startswith(".")]
class GreenSlothInitialize(App):
    """A Textual app fascilitate the model initialization process of GreenSloth"""
    
    def __init__(self):
        super().__init__()
        self.selected_model_path = None

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
        with ContentSwitcher(initial="start-page", id="content-mains"):
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
                    Label("Please select a Model directory", id="label-directoryselect"),
                    Button("Select", id="button-modelselect", variant="default", disabled=True),
                )
                yield ModelPathSelection("./", id="directory-editmodel")
                
            with Vertical(id="editmodel-functions-page"):
                yield Label("Model Name", id="label-editmodel-name")
                with ContentSwitcher(initial="editmodel-functions-buttons", id="content-editmodel-functions"):
                    with Vertical(id="editmodel-functions-buttons"):
                        yield HorizontalGroup(
                            Label("Extract Information from Model"),
                            Button("Extract", id="button-editmodel-modelinfo", variant="default")
                        )
                        yield HorizontalGroup(
                            Label("Compare Information with Model"),
                            Button("Compare", id="button-editmodel-compareinfo", variant="default")
                        )
                        yield HorizontalGroup(
                            Label("Update Information from Main Glossaries"),
                            Button("Update", id="button-editmodel-glossary", variant="default")
                        )
                        yield HorizontalGroup(
                            Label("Convert to Python"),
                            Button("Convert", id="button-editmodel-convertpython", variant="default")
                        )
                        yield HorizontalGroup(
                            Label("Convert to LaTeX"),
                            Button("Convert", id="button-editmodel-convertlatex", variant="default")
                        )
                    with Vertical(id="editmodel-functions-compare"):
                        yield HorizontalGroup(
                            Button("Back", id="button-editmodel-compare-back"),
                            Button("Extract and Compare", id="button-editmodel-compareagain", variant="default")
                        )
                        yield HorizontalGroup(
                            VerticalScroll(
                                Label("Variables", classes="title-compare"),
                                DataTable(id="datatable-variables")
                            ),
                            VerticalScroll(
                                Label("Parameters", classes="title-compare"),
                                DataTable(id="datatable-parameters")
                            )
                        )


    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
        
    def action_quit(self) -> None:
        self.exit()
        
    def action_starting_page(self) -> None:
        switcher = self.query_one("#content-mains", ContentSwitcher)
        switcher.current = "start-page"

    #### Buttons
    
    @on(Button.Pressed, "#button-switchpage-createmodel")
    def switch_to_create_model(self) -> None:
        switcher = self.query_one("#content-mains", ContentSwitcher)
        switcher.current = "create-model-page"

    @on(Button.Pressed, "#button-switchpage-editmodel")
    def switch_to_editmodel_select(self) -> None:
        switcher = self.query_one("#content-mains", ContentSwitcher)
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
            
    @on(Button.Pressed, "#button-modelselect")
    def switch_to_editmodel_funcs(self) -> None:
        switcher = self.query_one(ContentSwitcher)
        selected_dir = Path(self.query_one("#label-directoryselect", Label).content)
        self.app.selected_model_path = selected_dir
        
        label_modelname = self.query_one("#label-editmodel-name", Label)
        label_modelname.update(selected_dir.name)
        
        switcher.current = "editmodel-functions-page"
        
    @on(Button.Pressed, "#button-editmodel-modelinfo")
    def extract_model_info(self) -> None:
        
        model_path = self.app.selected_model_path
        model_name = self.app.selected_model_path.name
        
        installerfuncs.gs_extractinfo(
            model_dir=model_path,
            model_name=model_name
        )
        
        button = self.query_one("#button-editmodel-modelinfo", Button)
        button.variant = "success"
        button.label = "Extracted!"
        
        self.set_timer(3, lambda: reset_button(button, "Extract", "default"))
        
    @on(Button.Pressed, "#button-editmodel-compareinfo")
    def compare_model_info(self) -> None:
        switcher = self.query_one("#content-editmodel-functions", ContentSwitcher)
        switcher.current = "editmodel-functions-compare"
        
        compare_dict = installerfuncs.gs_compareinfos(
            model_dir=self.app.selected_model_path
        )
        
        table = self.query_one(f"#datatable-variables", DataTable)
        table.add_columns("Model", "Glossary")
        
        if len(compare_dict["variables"][0]) != 0 or len(compare_dict["variables"][1]) != 0:
            for var in compare_dict["variables"][0]:
                table.add_row(var, "")
            for var in compare_dict["variables"][1]:
                table.add_row("", var)

        # for name, (checked_model, checked_gloss) in compare_dict.items():
        #     table = self.query_one(f"#datatable-{name}", DataTable)
        #     table.add_columns("Model", "Glossary")
            
        #     if len(checked_model) != 0 or len(checked_gloss) != 0:
        #         for var in checked_model:
        #             table.add_row(var, "")
        #         for var in checked_gloss:
        #             table.add_row("", var)

    @on(Button.Pressed, "#button-editmodel-compare-back")
    def goback_editmodel_functions(self) -> None:
        switcher = self.query_one("#content-editmodel-functions", ContentSwitcher)
        switcher.current = "editmodel-functions-buttons"
        
    @on(Button.Pressed, "#button-editmodel-compareagain")
    def compare_again(self) -> None:
        self.compare_model_info()

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
    def update_create_model_directory_label(self, event: DirectoryTree.DirectorySelected) -> None:
        """Update the directory label with the selected path."""
        selected_dir = event.path
        self.query_one("#directory-label", Label).update(str(selected_dir) + "/")
    
    @on(DirectoryTree.DirectorySelected, "#directory-editmodel")
    def edit_model_directory_select(self, event: DirectoryTree.DirectorySelected) -> None:
        """Update the directory label with the selected path."""
        
        selected_dir = event.path
        select_button = self.query_one("#button-modelselect", Button)
        
        self.query_one("#label-directoryselect", Label).update(str(selected_dir) + "/")
        
        if Path.exists(selected_dir / "model_info"):
            select_button.variant = "success"
            select_button.disabled = False
        else:
            select_button.variant = "default"
            select_button.disabled = True

if __name__ == "__main__":
    app = GreenSlothInitialize()
    app.run()