# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/10_cli.ipynb.

# %% ../nbs/10_cli.ipynb 1
from __future__ import annotations
import json,shutil,warnings

from .read import *
from .sync import *
from .process import *
from .processors import *
from fastcore.utils import *
from fastcore.script import call_parse

# %% auto 0
__all__ = ['config_key', 'ghp_deploy', 'create_sidebar', 'FilterDefaults', 'filter_nb', 'create_quarto']

# %% ../nbs/10_cli.ipynb 4
def config_key(c, default=None, path=True):
    "Look for key `c` in settings.ini"
    cfg = get_config()
    if not c: raise ValueError(f'settings.ini not found')
    f = cfg.path if path else cfg.get
    res = f(c, default=default)
    if res is None: raise ValueError(f'`{c}` not specified in settings.ini')
    return res

# %% ../nbs/10_cli.ipynb 5
@call_parse
def ghp_deploy():
    "Deploy docs in doc_path from settings.ini to GitHub Pages"
    try: from ghp_import import ghp_import
    except:
        warnings.warn('Please install ghp-import with `pip install ghp-import`')
        return
    ghp_import(config_key('doc_path'), push=True, stderr=True, no_history=True)

# %% ../nbs/10_cli.ipynb 7
def _create_sidebar(
    path:str=None, symlinks:bool=False, file_glob:str='*.ipynb', file_re:str=None, folder_re:str=None, 
    skip_file_glob:str=None, skip_file_re:str=None, skip_folder_re:str='^[_.]'):
    path = config_key("nbs_path") if not path else Path(path)
    files = globtastic(path, symlinks=symlinks, file_glob=file_glob, file_re=file_re,
                       folder_re=folder_re, skip_file_glob=skip_file_glob,
                       skip_file_re=skip_file_re, skip_folder_re=skip_folder_re
                      ).sorted().map(Path)
    yml_path = path/'sidebar.yml'
    yml = "website:\n  sidebar:\n    contents:\n"
    yml += '\n'.join(f'      - {o.relative_to(path)}' for o in files)
    yml_path.write_text(yml)
    return files

# %% ../nbs/10_cli.ipynb 8
@call_parse
def create_sidebar(
    path:str=None, # path to notebooks
    symlinks:bool=False, # follow symlinks?
    file_glob:str='*.ipynb', # Only include files matching glob
    file_re:str=None, # Only include files matching regex
    folder_re:str=None, # Only enter folders matching regex
    skip_file_glob:str=None, # Skip files matching glob
    skip_file_re:str=None, # Skip files matching regex
    skip_folder_re:str='^[_.]' # Skip folders matching regex
):
    "Create sidebar.yml"
    _create_sidebar(path, symlinks, file_glob=file_glob, file_re=file_re, folder_re=folder_re,
                   skip_file_glob=skip_file_glob, skip_file_re=skip_file_re, skip_folder_re=skip_folder_re)

# %% ../nbs/10_cli.ipynb 10
class FilterDefaults:
    "Override `FilterDefaults` to change which notebook processors are used"
    def _nothing(self): return []
    xtra_procs=xtra_preprocs=xtra_postprocs=_nothing
    
    def base_preprocs(self): return [add_show_docs, insert_warning]
    def base_postprocs(self): return []
    def base_procs(self):
        return [strip_ansi, hide_line, filter_stream_, lang_identify, rm_header_dash,
                clean_show_doc, exec_show_docs, rm_export, clean_magics, hide_]

    def procs(self):
        "Processors for export"
        return self.base_procs() + self.xtra_procs()

    def preprocs(self):
        "Preprocessors for export"
        return self.base_preprocs() + self.xtra_preprocs()

    def postprocs(self):
        "Postprocessors for export"
        return self.base_postprocs() + self.xtra_postprocs()

# %% ../nbs/10_cli.ipynb 11
@call_parse
def filter_nb(
    nb_txt:str=None  # Notebook text (uses stdin if not provided)
):
    "A notebook filter for quarto"
    filt = get_config().get('exporter', FilterDefaults)()
    printit = False
    if not nb_txt: nb_txt,printit = sys.stdin.read(),True
    nb = dict2nb(json.loads(nb_txt))
    NBProcessor(nb=nb, procs=filt.procs(), preprocs=filt.preprocs(), postprocs=filt.postprocs()).process()
    res = nb2str(nb)
    if printit: print(res, flush=True)
    else: return res

# %% ../nbs/10_cli.ipynb 13
@call_parse
def create_quarto(
    path:str=None, # path to notebooks
    doc_path:str=None, # path to output docs
    symlinks:bool=False, # follow symlinks?
    file_glob:str='*.ipynb', # Only include files matching glob
    file_re:str=None, # Only include files matching regex
    folder_re:str=None, # Only enter folders matching regex
    skip_file_glob:str=None, # Skip files matching glob
    skip_file_re:str=None, # Skip files matching regex
    skip_folder_re:str='^[_.]' # Skip folders matching regex
):
    "Create quarto docs and README.md"
    path = config_key("nbs_path") if not path else Path(path)
    files = _create_sidebar(path, symlinks, file_glob=file_glob, file_re=file_re, folder_re=folder_re,
                   skip_file_glob=skip_file_glob, skip_file_re=skip_file_re, skip_folder_re=skip_folder_re)
    doc_path = config_key("doc_path") if not doc_path else Path(doc_path)
    os.system(f'cd {path} && quarto render')
    os.system(f'cd {path} && quarto render {files[-1]} -o README.md -t gfm')
    cfg_path = get_config().config_path
    shutil.rmtree(cfg_path/'docs', ignore_errors=True)
    (cfg_path/'README.md').unlink(missing_ok=True)
    docs = path/'docs'
    shutil.move(docs/'README.md', cfg_path)
    shutil.move(docs, cfg_path)
