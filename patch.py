import os
import requests
import zipfile
import io
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info(f"Starting font patching process with makegroups={args.makegroups}")

    # URL of the latest release
    url = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip"
    logger.info("Downloading latest Nerd Fonts patcher...")

    # Send HTTP request to the URL
    response = requests.get(url)

    # Make sure the request was successful
    assert response.status_code == 200, f"Failed to download patcher: HTTP {response.status_code}"
    logger.info("Successfully downloaded Nerd Fonts patcher")

    # Open the zip file in memory
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    # Extract the zip file
    logger.info("Extracting FontPatcher...")
    zip_file.extractall("FontPatcher")
    logger.info("FontPatcher extracted successfully")

    # list all files in the current directory
    files = os.listdir('Original')
    logger.info(f"Found {len(files)} files in Original directory")

    # change root dir to Ligaturizer
    os.chdir('Ligaturizer')
    logger.info("Changed working directory to Ligaturizer")

    os.makedirs("../Ligaturized", exist_ok=True)
    logger.info("Created Ligaturized directory")

    # 获取 Original 文件夹中的所有 .ttf 和 .otf 文件
    font_files = [f for f in os.listdir("../Original") if f.endswith(('.ttf', '.otf'))]
    logger.info(f"Found {len(font_files)} font files to process")

    def clean_font_name(filename):
        # 移除扩展名
        base_name = os.path.splitext(filename)[0]

        # 字体样式后缀列表
        style_suffixes = [
            # 复合样式 (最长的要最先处理)
            '-ExtraLightItalic', '-BlackItalic', '-BoldItalic', '-LightItalic', '-MediumItalic', '-RegularItalic', '-ThinItalic',
            '-ExtraBoldItalic', '-SemiBoldItalic',
            # 带分隔符的基础样式
            '-ExtraLight', '-ExtraBold', '-SemiBold', '-Regular', '-Medium', '-Light', '-Black', '-Bold', '-Thin', '-Italic',
            # 不带分隔符的样式 (注意顺序要和上面保持一致)
            'ExtraLight', 'ExtraBold', 'SemiBold', 'Regular', 'Medium', 'Light', 'Black', 'Bold', 'Thin', 'Italic',
            # 点号分隔的样式
            '.extralight', '.extrabold', '.semibold', '.regular', '.medium', '.light', '.black', '.bold', '.thin', '.italic',
            # 下划线分隔的样式
            '_ExtraLight', '_ExtraBold', '_SemiBold', '_Regular', '_Medium', '_Light', '_Black', '_Bold', '_Thin', '_Italic'
        ]

        # 按长度排序确保最长的后缀先被替换
        style_suffixes.sort(key=len, reverse=True)

        # 移除所有样式后缀
        cleaned_name = base_name
        for suffix in style_suffixes:
            cleaned_name = cleaned_name.replace(suffix, '')

        return cleaned_name

    # 第一阶段：添加连字
    logger.info("=== Stage 1: Adding Ligatures ===")
    for file in font_files:
        logger.info(f"Processing {file}...")
        if file in ["consolaz.ttf", "consolai.ttf", "consolab.ttf", "consola.ttf"]:
            output_name = file.replace("b.ttf", "").replace("i.ttf", "").replace("z.ttf", "").replace(".ttf", "")
            logger.info(f"Special handling for Consolas font: {output_name}")
        else:
            output_name = clean_font_name(file)
            logger.info(f"Cleaned font name: {output_name}")

        cmd = f'fontforge -lang py -script ligaturize.py "../Original/{file}" --output-dir="../Ligaturized/" --output-name="{output_name}"'
        logger.debug(f"Executing command: {cmd}")
        result = os.system(cmd)
        if result == 0:
            logger.info(f"Successfully added ligatures to {file}")
        else:
            logger.error(f"Failed to add ligatures to {file}")

    # 第二阶段：添加 Nerd Font 符号
    logger.info("\n=== Stage 2: Adding Nerd Font Symbols ===")
    os.chdir("../FontPatcher")
    files = os.listdir('../Ligaturized')
    os.makedirs("../Output", exist_ok=True)
    logger.info(f"Found {len(files)} ligaturized fonts to patch")

    for file in files:
        logger.info(f"Patching {file} with Nerd Font symbols...")
        cmd = f'fontforge -script font-patcher "../Ligaturized/{file}" --out "../Output/" --complete --makegroups {args.makegroups}'
        logger.debug(f"Executing command: {cmd}")
        result = os.system(cmd)
        if result == 0:
            logger.info(f"Successfully patched {file}")
        else:
            logger.error(f"Failed to patch {file}")

    logger.info("\n=== Font Processing Complete ===")
    logger.info(f"Output files can be found in the 'Output' directory")

if __name__ == "__main__":
    main()
