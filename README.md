# Consola-Nerd-Font-Ligaturized

Consola is property of Microsoft so it can't be redistributed here. But it is included in all versions of Windows. Here is a script to patch it. This can probably be used with other fonts too.

## How to use

1. Install git, fontforge and python3 eg with `winget install Git.Git FontForge.FontForge Python3`
2. Clone this repo with `git clone --recurse-submodules --remote-submodules https://github.com/C4illin/Consola-Nerd-Font-Ligaturized.git`
3. Locate the Consola font files on your system and copy them to `Original`
4. Run `python patch.py`
5. Install the patched font from the `Output` folder

### Use in VSCode

1. Set `"editor.fontFamily": "'LigaConsola Nerd Font', other fonts..."`
2. Set `"editor.fontLigatures": true,`
3. You may also set `"debug.console.fontFamily":` and `"terminal.integrated.fontFamily":`

## Update

1. Run `git pull`
2. Run `git submodule update --recursive --remote`
3. Run `python patch.py` which will also update the Nerd Font patcher
