import os
import re
import xml.etree.ElementTree as ET
import logging

# 指定目录
target_directory = '/opt/1panel/apps/openresty/openresty/www/sites/res.lengshanyun.top/index'

# 指定日志文件的路径
log_file_path = os.path.join(target_directory, 'extract_and_rename.log')

# 配置日志记录
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_spaces(xml_file):
    with open(xml_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 使用正则表达式删除每行的空格、制表符和换行符
    new_lines = [re.sub(r'\s+', '', line) for line in lines]

    # 将删除空格后的内容写回文件
    with open(xml_file, 'w', encoding='utf-8') as file:
        file.write('\n'.join(new_lines))

def rename_file(xml_file):
    full_path = os.path.abspath(xml_file)

    try:
        # 解析XML文件
        tree = ET.parse(full_path)
        root = tree.getroot()

        # 提取链接
        string_elements = root.findall(".//string")
        for string_element in string_elements:
            if 'https://res.lengshanyun.top/apps/' in string_element.text:
                extracted_url = string_element.text

                match = re.search(r'\d+', extracted_url)
                if match:
                    extracted_number = match.group()
                    new_filename = f'lengshan{extracted_number}.plist'

                    # 检查新文件名是否已存在
                    if not os.path.exists(new_filename):
                        os.rename(full_path, new_filename)
                        logging.info(f'喜报：文件已经成功重命名为：{new_filename}')
                    else:
                        logging.error(f'傻逼，这个文件 {new_filename} 已存在，你让我怎么重命名')
                    break  # 提取一次后退出循环
        else:
            logging.error('未找到匹配的链接信息')
    except Exception as e:
        logging.error(f'发生错误：{e}')

def main():
    for filename in os.listdir(target_directory):
        if filename.endswith('.plist'):  # 仅处理以 .plist 结尾的文件
            file_path = os.path.join(target_directory, filename)
            remove_spaces(file_path)
            rename_file(file_path)
