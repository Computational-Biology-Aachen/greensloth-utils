import os
from pathlib import Path
from typing import Optional
import importlib.util
from inspect import getmembers, isfunction
from mxlpy import Model
import sys
import pandas as pd

from GreenSlothUtils import extract_select_to_gloss, write_python_from_gloss, write_latex_from_model, write_ode_from_model

def iterate_files(path_to_scan: Path, model_name: str, target_dir: Path, dirs = "") -> None:

    for src_file in os.scandir(path_to_scan):
        if os.path.isdir(src_file):
            new_dirs = dirs
            new_dirs += src_file.name + '/'

            os.makedirs(
                target_dir / new_dirs,
                exist_ok=True
            )

            iterate_files(src_file, model_name, target_dir, dirs=new_dirs)

        elif os.path.isfile(src_file):
            with open(src_file, 'r') as f:
                content = f.read()
            if src_file.name.endswith(('.py', ".ipynb")):
                content = content.replace('{{MODEL_NAME}}', model_name)

            dest = target_dir / dirs / src_file.name

            with open(dest, 'w') as f:
                f.write(content)


def get_model(model_dir: Path, model_name: str) -> Model | None:
    spec = importlib.util.spec_from_file_location("model", model_dir / "model" / "__init__.py")
    if spec is None or spec.loader is None:
        msg = f"Cannot find spec for module {model_name}"
        raise ImportError(msg)

    module = importlib.util.module_from_spec(spec)
    sys.modules["model"] = module
    spec.loader.exec_module(module)

    for func in getmembers(module, isfunction):
        if func[0] == model_name:
            return func[1]()
    return None

def gs_install(
    model_name: str,
    target_dir: Optional[Path] = None,
) -> None:
    if target_dir is None:
        target_dir = Path('./')

    try:
        Path.mkdir(
            target_dir / model_name,
            parents=True,
            exist_ok=False
        )
    except FileExistsError:
        msg = f"There already exists a folder with name '{model_name}'"
        raise FileExistsError(msg) from None

    iterate_files(Path(__file__).parent / "modelinit", model_name, target_dir= target_dir / model_name)

    for i in ["model_glosses", "python_written/gloss_to_python", "python_written/model_to_latex"]:
        try:
            Path.mkdir(target_dir / model_name / "model_info" / i, parents=True, exist_ok=True)
        except FileExistsError:
            msg_0 = "Something went wrong!"
            raise FileExistsError(msg_0) from None

def gs_extractinfo(
    model_dir: Path,
    model_name: str
) -> None:
    
    modelinfo_dir = model_dir / "model_info"
    modelgloss_dir = modelinfo_dir / "model_glosses"
    
    model = get_model(
        model_dir=model_dir,
        model_name=model_name
    )
    
    extract_select_to_gloss(
            select=model.get_raw_variables(),
            column_names=[
                "Name",
                "Common Abbr.",
                "Paper Abbr.",
                "KEGG ID",
                "Python Var",
                "Glossary ID",
            ],
            pythonvar_col="Python Var",
            path_to_write= modelgloss_dir / "model_comps.txt",
        )
    
    extract_select_to_gloss(
            select=model.get_parameter_values(),
            column_names=[
                "Short Description",
                "Common Abbr.",
                "Paper Abbr.",
                "Value",
                "Unit",
                "Python Var",
                "Reference",
            ],
            pythonvar_col="Python Var",
            path_to_write= modelgloss_dir / "model_params.txt",
            value_col="Value"
        )
    
    surr_outputs_dict = {}
    for surr in model.get_raw_surrogates().values():
        for output in surr.outputs:
            surr_outputs_dict[output] = None
    full_dict = model.get_derived_variables() | surr_outputs_dict | model.get_raw_readouts()
    extract_select_to_gloss(
        select=full_dict,
        column_names=[
            "Name",
            "Common Abbr.",
            "Paper Abbr.",
            "KEGG ID",
            "Python Var",
            "Glossary ID",
        ],
        pythonvar_col="Python Var",
        path_to_write= modelgloss_dir / "model_derived_comps.txt",
    )

    extract_select_to_gloss(
        select=model.get_derived_parameters(),
        column_names=["Short Description", "Common Abbr.", "Paper Abbr.", "Python Var"],
        pythonvar_col="Python Var",
        path_to_write= modelgloss_dir / "model_derived_params.txt",
    )
    
    extract_select_to_gloss(
        select=model._reactions,
        column_names=[
            "Short Description",
            "Common Abbr.",
            "Paper Abbr.",
            "KEGG ID",
            "Python Var",
            "Glossary ID",
        ],
        pythonvar_col="Python Var",
        path_to_write= modelgloss_dir / "model_rates.txt",
    )
    
def gs_compareinfos(
    model_dir: Path
) -> dict:
    
    res_dict = {}
    
    modelinfo_dir = model_dir / "model_info"
    modelgloss_dir = modelinfo_dir / "model_glosses"
    
    for key, name in zip(["comps", "rates", "params", "derived_comps", "derived_params"], ["variables", "rates", "parameters", "derivedvars", "derivedparams"]):
        from_model=modelgloss_dir / f"model_{key}.csv"
        edit_gloss=modelinfo_dir / f"{key}.csv"
        
        df_model = pd.read_csv(from_model, keep_default_na=False)
        df_gloss = pd.read_csv(edit_gloss, keep_default_na=False)
        
        checked_model = set(df_model["Python Var"]) - set(df_gloss["Python Var"])
        checked_gloss = set(df_gloss["Python Var"]) - set(df_model["Python Var"])
        
        if len(checked_model) != 0 or len(checked_gloss) != 0:
            res_dict[name] = (checked_model, checked_gloss)
        else:
            res_dict[name] = (set(), set())
        
    return res_dict

def gs_writepython(
    model_dir: Path,
) -> None:
    
    modelinfo_dir = model_dir / "model_info"
    glosstopython_dir = modelinfo_dir / "python_written" / "gloss_to_python"
    
    for i in ["comps", "rates", "params", "derived_comps", "derived_params"]:
        write_python_from_gloss(
            path_to_write=glosstopython_dir / f'{i}.txt',
            path_to_glass=modelinfo_dir / f'{i}.csv',
            var_list_name=f'{i}_table'
        )
        
def gs_writelatex(
    model_dir: Path,
) -> None:
    
    modelinfo_dir = model_dir / "model_info"
    modeltolatex_dir = modelinfo_dir / "python_written" / "model_to_latex"
    
    model = get_model(
        model_dir=model_dir,
        model_name=model_dir.name
    )
    
    for i in ["rates", "derived_comps", "derived_params"]:
        write_latex_from_model(
            m=model,
            write_path=modeltolatex_dir / f"{i}.txt",
            gloss_path=modelinfo_dir / f"{i}.csv",
        )
        
    write_ode_from_model(m=model, path_to_write=modeltolatex_dir / "model_odes.txt")