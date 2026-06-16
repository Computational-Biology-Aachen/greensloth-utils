from collections.abc import Iterable
from pathlib import Path
from itertools import zip_longest
import pyclip

from textual import on
from textual.app import App, ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalScroll,
    VerticalGroup,
    CenterMiddle
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
    DataTable,
    TabbedContent,
    TabPane,
    TextArea
)

from GreenSlothUtils import installerfuncs
    

def reset_button(button: Button, label: str, color: str) -> None:
    button.label = label
    button.variant = color

def press_button(self, button: Button, new_label: str) -> None:
    button.variant = "success"
    old_label = str(button.label)
    old_color = button.variant
    button.label = new_label

    self.set_timer(3, lambda: reset_button(button, old_label, old_color))

class ModelPathSelection(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if not path.name.startswith(".")]
    
class ModelCreationView(Vertical):
    """A self-contained widget for creating a model."""
    
    def __init__(self, is_guide_mode: bool = False, *args, **kwargs):
        # Pass standard arguments (like 'id' or 'classes') up to the parent Vertical container
        super().__init__(*args, **kwargs)
        
        # Save our custom flag so the rest of the class can see it
        self.is_guide_mode = is_guide_mode

    def compose(self) -> ComposeResult:
        # Note: You don't need highly specific IDs anymore if this widget 
        # manages its own events, but you can keep them if you prefer.
        yield HorizontalGroup(
            Button("Up Dir", id="button-create-updir", variant="primary"),
            Label("Please select a directory", id="directory-label"),
            Input(
                placeholder="Enter Model Name...",
                validators=[Regex(r"^[A-Z][a-zA-Z]*[0-9]{4}$")],
                restrict=r"[a-zA-Z0-9]*",
                id="input-modelname"
            ),
            Button("Create", id="button-modelcreate", disabled=True),
        )
        yield ModelPathSelection(Path("./").resolve(), id="create-model-directory")
        
    def reset_view(self) -> None:
        """Resets all child widgets to their initial default state."""
        # 1. Reset the text input and its validation styling
        name_input = self.query_one("#input-modelname", Input)
        name_input.value = ""
        name_input.remove_class("valid", "invalid")
        
        # 2. Reset the directory tree to the absolute current path
        tree = self.query_one("#create-model-directory", ModelPathSelection)
        default_path = Path("./").resolve()
        tree.path = default_path
        
        # 3. Reset the directory label
        label = self.query_one("#directory-label", Label)
        label.update(f"Please select a Model Path")
        
        # 4. Reset the create button to disabled/default
        create_button = self.query_one("#button-modelcreate", Button)
        create_button.label = "Create"
        create_button.variant = "default"
        create_button.disabled = True
        create_button.remove_class("confirm-flag")
        
    @on(Button.Pressed, "#button-create-updir")
    def navigate_up_create_tree(self) -> None:
        tree = self.query_one("#create-model-directory", ModelPathSelection)
        label = self.query_one("#directory-label", Label)
        
        # Step back to the parent directory
        new_path = tree.path.resolve().parent
        tree.path = new_path
        
        # Update the UI label to reflect the new root
        label.update(f"{new_path}/")
        
    @on(Button.Pressed, "#button-modelcreate")
    def create_model(self) -> None:
        model_name = self.query_one("#input-modelname", Input).value
        model_path = Path(self.query_one("#directory-label", Label).content)
        create_button = self.query_one("#button-modelcreate", Button)
        directory_tree = self.query_one("#create-model-directory", ModelPathSelection)
        
        if create_button.has_class("confirm-flag"):
            # Update the main App's selected model state
            self.app.selected_model_path = model_path
            
            if self.is_guide_mode:
                # ---> Guide Behavior <---
                # Advance the step-by-step switcher directly to Step 2
                step_switcher = self.app.query_one("#content-stepbystep", ContentSwitcher)
                step_switcher.current = "step2"
            else:
                # ---> Main Menu Behavior <---
                # Update the edit page label and switch the main view
                self.app.query_one("#label-editmodel-name", Label).update(model_path.name)
                self.app.query_one("#content-mains", ContentSwitcher).current = "editmodel-functions-page"
            
            return
        
        # Add logic to create the model
        if not Path.is_dir(model_path):
            # Handle the case where the selected path is not a directory
            create_button.variant = "error"
            create_button.label = "Invalid Directory"
        elif Path.exists(model_path / model_name):
            create_button.variant = "error"
            create_button.label = "Model Already Exists"
        elif Path.exists(model_path / "model_info"):
            create_button.variant = "warning"
            create_button.label = "Select this model instead?"
            create_button.add_class("confirm-flag")
        else:
            installerfuncs.gs_install(model_name, Path(model_path))
            press_button(self, create_button, "Created!")
            directory_tree.reload()
            
    @on(DirectoryTree.DirectorySelected, "#create-model-directory")
    def update_create_model_directory_label(self, event: DirectoryTree.DirectorySelected) -> None:
        """Update the directory label with the selected path."""
        selected_dir = event.path
        self.query_one("#directory-label", Label).update(str(selected_dir) + "/")
        create_button = self.query_one("#button-modelcreate", Button)
        
        if Path.exists(selected_dir / "model_info"):
            create_button.disabled = False
            create_button.variant = "warning"
            create_button.label = "Select this model instead?"
            create_button.add_class("confirm-flag")
        else:
            create_button.disabled = True
        
    @on(Input.Changed, "#input-modelname")
    def check_modelname(self) -> None:
        input_modelname = self.query_one("#input-modelname", Input)
        create_button = self.query_one("#button-modelcreate", Button)
        
        if input_modelname.is_valid:
            input_modelname.add_class("valid")
            input_modelname.remove_class("invalid")
            create_button.disabled = False
        else:
            input_modelname.add_class("invalid")
            input_modelname.remove_class("valid")
            create_button.disabled = True
    
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
                
            yield ModelCreationView(id="create-model-page")
                
            with Vertical(id="editmodel-select-page"):
                yield HorizontalGroup(
                    Label("Please select a Model directory", id="label-directoryselect"),
                    Button("Select", id="button-modelselect", variant="default", disabled=True),
                )
                yield ModelPathSelection("./", id="directory-editmodel")
                
            with Vertical(id="editmodel-functions-page", classes="center-text"):
                yield CenterMiddle(Label("Model Name", id="label-editmodel-name"), classes="head-row")
                with ContentSwitcher(initial="editmodel-functions-buttons", id="content-editmodel-functions"):
                    with Vertical(id="editmodel-functions-buttons"):
                        yield Button("Extract Information from Model", id="button-editmodel-extraction", variant="default", classes="equal-width")
                        yield Button("Update Information from Main Glossaries", id="button-editmodel-glossary", variant="default", classes="equal-width")
                        yield Button("Convert to Python", id="button-editmodel-convertpython", variant="default", classes="equal-width")
                        yield Button("Convert to LaTeX", id="button-editmodel-convertlatex", variant="default", classes="equal-width")
                        
                    with Vertical(id="editmodel-functions-compare"):
                        yield HorizontalGroup(
                            Button("Back", id="button-editmodel-compare-back", classes="equal-width"),
                            Button("Extract and Compare", id="button-editmodel-compareagain", variant="default", classes="equal-width"),
                            classes="head-row"
                        )
                        
                        with HorizontalGroup():
                            yield Label("Double-Click a cell to copy its value!", classes="low-text")
                            yield Button("?", id="button-editmodel-comparehelp", classes="hint-icon", tooltip="This shows the difference between the csv tables extracted from the model and the ones you have to fill. It only shows the Python Vars.")
                        with TabbedContent(initial="tab-variables"):
                            with TabPane("Variables", id="tab-variables", classes="has-no-data"):
                                yield DataTable(id="datatable-variables")
                            with TabPane("Rates", id="tab-rates", classes="has-no-data"):
                                yield DataTable(id="datatable-rates")
                            with TabPane("Parameters", id="tab-parameters", classes="has-no-data"):
                                yield DataTable(id="datatable-parameters")
                            with TabPane("Derived Variables", id="tab-derivedvars", classes="has-no-data"):
                                yield DataTable(id="datatable-derivedvars")
                            with TabPane("Derived Parameters", id="tab-derivedparams", classes="has-no-data"):
                                yield DataTable(id="datatable-derivedparams")
                
            with Vertical(id="stepbystep-createmodel-page"):
                yield CenterMiddle(Label("Step-by-Step"), classes="head-row")
                yield HorizontalGroup(
                            Button("Previous Step", id="button-stepguide-prev", classes="equal-width"),
                            Button("Next Step", id="button-stepguide-next", classes="equal-width")
                        )
                with ContentSwitcher(initial="step0", id="content-stepbystep"):
                    with Vertical(id="step0", classes="center-children"):
                        yield Label("Step 0: What is this?")
                        yield TextArea(
                            """To create a model for GreenSloth, this step-by-step guide can help with making it ready for deployment. This step-by-step guide only consists of 8 steps, however, they each differ dramatically in complexity and effort. If you cannot finish the steps in one sitting, do not worry, as you can always go back to where you were by just clicking the next step button. At the end of these steps, you will have a model in mxlpy that has similar nomenclature and format as the other models in the database. Additionally, your model will have a script to create a well-formed documentation for your model. One that can also be suplied to publications.
                            
                            Once you are ready, you can begin, by pressign the Next Step button.
                            """,
                            read_only=True
                        )
                    with Vertical(id="step1", classes="center-children"):
                        yield Label("Step 1: Create Model Directory")
                        yield ModelCreationView(is_guide_mode=True, id="create-model-page-guide")
                    with Vertical(id="step2", classes="center-children"):
                        yield Label("Step 2: Create Model using MxLpy")
                    with Vertical(id="step3", classes="center-children"):
                        yield Label("Step 3: Extract Model Information")
                    with Vertical(id="step4", classes="center-children"):
                        yield Label("Step 4: Correct Model Information")
                    with Vertical(id="step5", classes="center-children"):
                        yield Label("Step 5: Update Info from Main Glossaries")
                    with Vertical(id="step6", classes="center-children"):
                        yield Label("Step 6: Correct Model Information again")
                    with Vertical(id="step7", classes="center-children"):
                        yield Label("Step 7: Extract Model Information for README")
                    with Vertical(id="step8", classes="center-children"):
                        yield Label("Step 8: Finish up README")
                            

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
        # 1. Find the view instance and reset it
        create_view = self.query_one("#create-model-page", ModelCreationView)
        create_view.reset_view()
        
        # 2. Make the switch
        switcher = self.query_one("#content-mains", ContentSwitcher)
        switcher.current = "create-model-page"

    @on(Button.Pressed, "#button-switchpage-editmodel")
    def switch_to_editmodel_select(self) -> None:
        switcher = self.query_one("#content-mains", ContentSwitcher)
        switcher.current = "editmodel-select-page"
        
    @on(Button.Pressed, "#button-stepguide")
    def switch_to_stepbystep_select(self) -> None:
        switcher = self.query_one("#content-mains", ContentSwitcher)
        switcher.current = "stepbystep-createmodel-page"
            
    @on(Button.Pressed, "#button-modelselect")
    def switch_to_editmodel_funcs(self) -> None:
        switcher = self.query_one(ContentSwitcher)
        selected_dir = Path(self.query_one("#label-directoryselect", Label).content)
        self.app.selected_model_path = selected_dir
        
        label_modelname = self.query_one("#label-editmodel-name", Label)
        label_modelname.update(selected_dir.name)
        
        switcher.current = "editmodel-functions-page"
        
    @on(Button.Pressed, "#button-editmodel-extraction")
    def extract_model_info(self, keep_button: bool = False) -> None:
        
        model_path = self.app.selected_model_path
        model_name = self.app.selected_model_path.name
        
        installerfuncs.gs_extractinfo(
            model_dir=model_path,
            model_name=model_name
        )
        
        compare_dict = installerfuncs.gs_compareinfos(
            model_dir=self.app.selected_model_path
        )
        
        for name, (checked_model, checked_gloss) in compare_dict.items():
            # Bulletproof way to find the generated Tab without guessing prefixes
            tab_widget = None
            for tab in self.query("Tab"):  # Ask Textual for all Tab widgets
                if tab.id and tab.id.endswith(name):
                    tab_widget = tab
                    break
            
            table = self.query_one(f"#datatable-{name}", DataTable)
            table.clear(columns=True)
        
            for column_header in ["Model", "Glossary"]:
                table.add_column(column_header)
        
            if len(checked_model) != 0 or len(checked_gloss) != 0:
                tab_widget.remove_class("has-no-data")
                tab_widget.add_class("has-data")
                for model_val, gloss_val in zip_longest(checked_model, checked_gloss, fillvalue=""):
                    table.add_row(model_val, gloss_val)
                    
            else:
                tab_widget.remove_class("has-data")
                tab_widget.add_class("has-no-data")
                
        switcher = self.query_one("#content-editmodel-functions", ContentSwitcher)
        switcher.current = "editmodel-functions-compare"
        
        press_button(
            self,
            self.query_one("#button-editmodel-compareagain", Button),
            "Extracted!",
        )

    @on(Button.Pressed, "#button-editmodel-compare-back")
    def goback_editmodel_functions(self) -> None:
        switcher = self.query_one("#content-editmodel-functions", ContentSwitcher)
        switcher.current = "editmodel-functions-buttons"
        
    @on(Button.Pressed, "#button-editmodel-compareagain")
    def compare_again(self) -> None:
        self.extract_model_info()
        
    @on(Button.Pressed, "#button-editmodel-convertpython")
    def convert_to_python(self) -> None:
        installerfuncs.gs_writepython(
            model_dir=self.app.selected_model_path
        )
        
        press_button(
            self,
            self.query_one("#button-editmodel-convertpython", Button),
            "Converted!",
        )
        
    @on(Button.Pressed, "#button-editmodel-convertlatex")
    def convert_to_latex(self) -> None:
        installerfuncs.gs_writelatex(
            model_dir=self.app.selected_model_path
        )
        
        press_button(
            self,
            self.query_one("#button-editmodel-convertlatex", Button),
            "Converted!",
        )
        
    @on(Button.Pressed, "#button-stepguide-prev")
    def stepguide_prev(self) -> None:
        create_view = self.query_one("#create-model-page-guide", ModelCreationView)
        create_view.reset_view()
        
        switcher = self.query_one("#content-stepbystep", ContentSwitcher)
        page_ids = [page.id for page in switcher.children]
        switcher_idx = page_ids.index(switcher.current)
        
        if switcher_idx > 0:
            switcher.current = page_ids[switcher_idx - 1]
            
    @on(Button.Pressed, "#button-stepguide-next")
    def stepguide_next(self) -> None:
        create_view = self.query_one("#create-model-page-guide", ModelCreationView)
        create_view.reset_view()
        
        switcher = self.query_one("#content-stepbystep", ContentSwitcher)
        page_ids = [page.id for page in switcher.children]
        switcher_idx = page_ids.index(switcher.current)
        
        if switcher_idx < len(page_ids) - 1:
            switcher.current = page_ids[switcher_idx + 1]

    ### Input Events
    
    

    ### Directory Tree Events
    
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
            
    ### DataTable Events
    
    @on(DataTable.CellSelected)
    def copy_cell_to_clipboard(self, event: DataTable.CellSelected) -> None:
        """Fires when a cell is clicked or selected with Enter."""
        
        cell_value = str(event.value)
        
        if not cell_value.strip():
            return
        
        pyclip.copy(cell_value)
        
        self.notify(f"Copied to clipboard: '{cell_value}'", title="Clipboard", severity="information")
        

if __name__ == "__main__":
    app = GreenSlothInitialize()
    app.run()
