import os
import requests
import zipfile
import io
import argparse
import logging
import concurrent.futures
import shutil
from pathlib import Path
import subprocess
import re
from functools import lru_cache
import sys
import platform

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def download_with_progress(url, cache_path, chunk_size=8192):
    """使用分块下载提升大文件下载性能，支持缓存"""
    # 检查缓存
    if os.path.exists(cache_path):
        logger.info("Using cached FontPatcher.zip from %s", cache_path)
        with open(cache_path, 'rb') as f:
            return f.read()

    # 下载文件
    logger.info("Cache not found, downloading from %s", url)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    content = io.BytesIO()
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0

    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            content.write(chunk)
            downloaded_size += len(chunk)
            if total_size:
                progress = (downloaded_size / total_size) * 100
                logger.info("Download progress: %.1f%%", progress)

    # 保存到缓存
    content_bytes = content.getvalue()
    logger.info("Saving %d bytes to cache: %s", len(content_bytes), cache_path)
    with open(cache_path, 'wb') as f:
        f.write(content_bytes)

    return content_bytes

def parse_args():
    parser = argparse.ArgumentParser(description='Patch fonts with ligatures and Nerd Font symbols')
    parser.add_argument('--makegroups',
                       type=int,
                       default=4,
                       choices=range(-1, 7),
                       help='''Font naming scheme (default: 4):
                           -1: Keep original names and versions
                           0: Use old naming scheme
                           1: Full Nerd Font name
                           2: Nerd Font with condensed family names
                           3: Nerd Font with condensed family and style names
                           4: NF with full names (default)
                           5: NF with condensed family names
                           6: NF with condensed family and style names''')
    parser.add_argument('--workers',
                       type=int,
                       default=4,
                       help='Number of workers for parallel processing')
    return parser.parse_args()

def clean_directory(path):
    """清理目录内容"""
    if os.path.exists(path):
        logger.info("Cleaning directory: %s", path)
        shutil.rmtree(path)
    os.makedirs(path)
    logger.info("Created clean directory: %s", path)

def process_font_ligatures(font_file, output_dir, output_name):
    """处理单个字体的连字"""
    try:
        logger.info("Processing ligatures for %s -> %s", font_file, output_name)
        cmd = ['fontforge', '-lang', 'py', '-script', 'ligaturize.py',
               str(font_file),
               f"--output-dir={output_dir}",
               f"--output-name={output_name}"]

        logger.debug("Executing command: %s", ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✓ Successfully added ligatures to %s", font_file)
            return True
        else:
            logger.error("✗ Failed to add ligatures to %s: %s", font_file, result.stderr)
            return False
    except Exception as e:
        logger.error("✗ Error processing %s: %s", font_file, str(e))
        return False

def process_nerd_font(font_file, output_dir, makegroups):
    """处理单个字体的 Nerd Font 符号"""
    try:
        logger.info("Adding Nerd Font symbols to %s", font_file)

        # 获取当前工作目录
        current_dir = Path.cwd()

        # 将输入和输出路径转换为相对路径
        rel_font_file = os.path.relpath(font_file, current_dir)
        rel_output_dir = os.path.relpath(output_dir, current_dir)

        logger.info("Using relative paths:")
        logger.info("- Input: %s", rel_font_file)
        logger.info("- Output: %s", rel_output_dir)

        cmd = ['fontforge', '-script', 'font-patcher',
               rel_font_file,
               '--out', rel_output_dir,
               '--complete',
               '--careful',
               '--makegroups', str(makegroups)]

        logger.info("Executing command: %s", ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✓ Successfully patched %s", font_file)
            return True
        else:
            if "Font generation failed" in result.stderr or "glyph named" in result.stderr:
                logger.warning("First attempt failed, retrying with quiet mode...")
                cmd.extend(['--quiet', '--force'])
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("✓ Successfully patched %s (second attempt)", font_file)
                    return True
                else:
                    logger.error("✗ Failed to patch %s (both attempts): %s", font_file, result.stderr)
                    return False
            else:
                logger.error("✗ Failed to patch %s: %s", font_file, result.stderr)
                return False
    except Exception as e:
        logger.error("✗ Error patching %s: %s", font_file, str(e))
        return False

@lru_cache(maxsize=128)
def clean_font_name(filename):
    """使用缓存和正则表达式优化字体名称清理"""
    base_name = Path(filename).stem

    # 使用预编译的正则表达式
    style_pattern = re.compile(r'[-_.]?(Extra[LB]ight|Black|Bold|Light|Medium|Regular|SemiBold|Thin|Italic)', re.IGNORECASE)
    compound_pattern = re.compile(r'[-_.]?(Extra[LB]ightItalic|BlackItalic|BoldItalic|LightItalic|MediumItalic|RegularItalic|ThinItalic|SemiBoldItalic)', re.IGNORECASE)

    # 先处理复合样式
    cleaned_name = compound_pattern.sub('', base_name)
    # 再处理基础样式
    cleaned_name = style_pattern.sub('', cleaned_name)

    return cleaned_name

def find_fonts(directory):
    """查找目录中的字体文件
    使用正则表达式匹配字体文件，支持 .ttf 和 .otf
    """
    pattern = re.compile(r'.*\.(ttf|otf)$', re.IGNORECASE)
    return sorted(
        f for f in Path(directory).iterdir()
        if f.is_file() and pattern.match(f.name)
    )

def main():
    args = parse_args()
    logger.info("=== Starting Font Patching Process ===")
    logger.info("Configuration:")
    logger.info("- Make Groups: %d", args.makegroups)
    logger.info("- Workers: %d", args.workers)
    logger.info("- Python Version: %s", sys.version.split()[0])
    logger.info("- Platform: %s", platform.platform())

    # 获取脚本所在目录作为工作目录
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)
    logger.info("Working directory: %s", script_dir)

    # 创建所有需要的目录的绝对路径
    font_patcher_dir = script_dir / 'FontPatcher'
    cache_dir = script_dir / '.cache'
    ligaturized_dir = script_dir / 'Ligaturized'
    output_dir = script_dir / 'Output'
    original_dir = script_dir / 'Original'
    ligaturizer_dir = script_dir / 'Ligaturizer'

    # 创建并清理目录
    logger.info("\n=== Preparing Directories ===")
    font_patcher_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)
    clean_directory(str(ligaturized_dir))
    clean_directory(str(output_dir))

    # 下载并解压 FontPatcher
    logger.info("\n=== Downloading Font Patcher ===")
    url = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip"
    cache_path = cache_dir / 'FontPatcher.zip'

    try:
        content = download_with_progress(url, cache_path)
        logger.info("Extracting FontPatcher.zip...")
        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
            zip_file.extractall(str(font_patcher_dir))
        logger.info("✓ FontPatcher extracted successfully")
    except Exception as e:
        logger.error("✗ Failed to download or extract patcher: %s", str(e))
        return

    # 获取字体文件列表
    logger.info("Looking for fonts in: %s", original_dir)

    if not original_dir.exists():
        logger.error("✗ Original directory not found at: %s", original_dir)
        return

    # 搜索字体文件
    font_files = find_fonts(original_dir)

    # 输出详细的搜索信息
    logger.info("Search details:")
    logger.info("- TTF files found: %d", sum(1 for f in font_files if f.suffix.lower() == '.ttf'))
    logger.info("- OTF files found: %d", sum(1 for f in font_files if f.suffix.lower() == '.otf'))

    if not font_files:
        logger.error("✗ No font files found in Original directory: %s", original_dir)
        logger.error("Please place your font files in the Original directory")
        # 列出目录中的所有文件以帮助诊断
        logger.info("Files in Original directory:")
        for file in original_dir.iterdir():
            logger.info("  - %s", file.name)
        return

    logger.info("\nFound %d font files to process:", len(font_files))
    for font in font_files:
        logger.info("- %s", font.name)

    # 第一阶段：并行添加连字
    logger.info("\n=== Stage 1: Adding Ligatures ===")
    os.chdir(ligaturizer_dir)
    logger.info("Changed working directory to: %s", os.getcwd())

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for font_file in font_files:
            if font_file.name in ["consolaz.ttf", "consolai.ttf", "consolab.ttf", "consola.ttf"]:
                output_name = font_file.stem.replace("b", "").replace("i", "").replace("z", "")
                logger.info("Special handling for Consolas font: %s -> %s", font_file.name, output_name)
            else:
                output_name = clean_font_name(font_file.name)
                logger.info("Processing font: %s -> %s", font_file.name, output_name)

            futures.append(
                executor.submit(process_font_ligatures,
                              str(original_dir / font_file.name),
                              str(ligaturized_dir),
                              output_name)
            )

        completed = 0
        total = len(futures)
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            logger.info("Progress: %d/%d fonts processed (%.1f%%)",
                       completed, total, (completed/total)*100)

    # 第二阶段：并行添加 Nerd Font 符号
    logger.info("\n=== Stage 2: Adding Nerd Font Symbols ===")
    os.chdir(font_patcher_dir)
    logger.info("Changed working directory to: %s", os.getcwd())

    # 分别搜索 ttf 和 otf 文件
    ttf_files = list(ligaturized_dir.glob('*.ttf'))
    otf_files = list(ligaturized_dir.glob('*.otf'))
    ligaturized_files = ttf_files + otf_files

    logger.info("Found %d ligaturized fonts to patch:", len(ligaturized_files))
    for font in ligaturized_files:
        logger.info("- %s", font.name)

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for font_file in ligaturized_files:
            futures.append(
                executor.submit(process_nerd_font,
                              str(font_file),
                              str(output_dir),
                              args.makegroups)
            )

        completed = 0
        total = len(futures)
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            logger.info("Progress: %d/%d fonts processed (%.1f%%)",
                       completed, total, (completed/total)*100)

    logger.info("\n=== Font Processing Complete ===")
    # 分别搜索 ttf 和 otf 文件
    ttf_files = list(output_dir.glob('*.ttf'))
    otf_files = list(output_dir.glob('*.otf'))
    output_files = ttf_files + otf_files

    logger.info("Successfully processed %d fonts", len(output_files))
    logger.info("Output files:")
    for font in output_files:
        logger.info("- %s", font.name)
    logger.info("\nOutput files can be found in the 'Output' directory")

if __name__ == "__main__":
    main()
