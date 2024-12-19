# Consolas-Nerd-Font-Ligaturized

Consolas is property of Microsoft so it can't be redistributed here. But it is included in all versions of Windows. Here is a script to patch it. This can probably be used with other fonts too.

## How to use

1. Install git, fontforge and python3 eg with `winget install Git.Git FontForge.FontForge Python3`. Add FontForge bin folder to PATH.
2. Clone this repo with `git clone --recurse-submodules --remote-submodules https://github.com/C4illin/Consolas-Nerd-Font-Ligaturized.git` (this will take a while)
3. Locate the four Consolas font files on your system and copy them to `Original`
4. Run `python patch.py`
5. Install the patched font from the `Output` folder

### Use in VSCode

1. Set `"editor.fontFamily": "'LigaConsola Nerd Font', ...`
2. Set `"editor.fontLigatures": true,`
3. You may also set `"debug.console.fontFamily":` and `"terminal.integrated.fontFamily":`

## Update

1. Run `git pull`
2. Run `git submodule update --recursive --remote`
3. Run `python patch.py` which will also update the Nerd Font patcher

## Font Naming Options

The `--makegroups` parameter controls how the patched font will be named. Below are the different values and their effects:

Original font name example: Hugo Sans Mono ExtraCondensed Light Italic

| Value | Result Example | NF | Family | Aggregation |
|-------|---------------|:--:|:------:|:-----------:|
| -1 | *Keep original names and versions* | --- | --- | --- |
| 0 | *Use old naming scheme* | [-] | [-] | [-] |
| 1 | HugoSansMono Nerd Font ExtraCondensed Light Italic | [ ] | [ ] | [ ] |
| 2 | HugoSansMono Nerd Font ExtCn Light Italic | [ ] | [X] | [ ] |
| 3 | HugoSansMono Nerd Font XCn Lt It | [ ] | [X] | [X] |
| 4 | HugoSansMono NF ExtraCondensed Light Italic | [X] | [ ] | [ ] |
| 5 | HugoSansMono NF ExtCn Light Italic | [X] | [X] | [ ] |
| 6 | HugoSansMono NF XCn Lt It | [X] | [X] | [X] |

Where:
- NF: Use "NF" abbreviation instead of "Nerd Font"
- Family: Aggregate family names (e.g., "ExtraCondensed" -> "ExtCn")
- Aggregation: Further aggregate style names (e.g., "Light Italic" -> "Lt It")

Default value is 1, which uses the most complete naming scheme. Higher values result in shorter names.
