import os
import requests
import zipfile
import io

# URL of the latest release
url = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip"

# Send HTTP request to the URL
response = requests.get(url)

# Make sure the request was successful
assert response.status_code == 200

# Open the zip file in memory
zip_file = zipfile.ZipFile(io.BytesIO(response.content))

# Extract the zip file
zip_file.extractall("FontPatcher")

# list all files in the current directory
files = os.listdir('Original')
# change root dir to Ligaturizer
os.chdir('Ligaturizer')

os.makedirs("../Ligaturized", exist_ok=True)

# 获取 Original 文件夹中的所有 .ttf 和 .otf 文件
font_files = [f for f in os.listdir("../Original") if f.endswith(('.ttf', '.otf'))]

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

for file in font_files:
    if file in ["consolaz.ttf", "consolai.ttf", "consolab.ttf", "consola.ttf"]:
        output_name = file.replace("b.ttf", "").replace("i.ttf", "").replace("z.ttf", "").replace(".ttf", "")
    else:
        output_name = clean_font_name(file)
    
    os.system(
        f'fontforge -lang py -script ligaturize.py "../Original/{file}" --output-dir="../Ligaturized/" --output-name="{output_name}"'
    )
    
os.chdir("../FontPatcher")
files = os.listdir('../Ligaturized')
os.makedirs("../Output", exist_ok=True)
for file in files:
    os.system(
        f'fontforge -script font-patcher "../Ligaturized/{file}" --out "../Output/" --complete --makegroups 4'
    )
