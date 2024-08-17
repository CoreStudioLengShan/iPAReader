import zipfile
import plistlib
import os
import shutil
import lief

# 保持唯一性
unique_id = 0


def parse_macho_and_get_info(ipa_zip, exe_path):
    try:
        exe_data = ipa_zip.read(exe_path)
        macho = lief.parse(exe_data)

        # 获取架构信息
        arch = find_arch(macho)

        # 获取加密信息
        is_encrypted = is_encrypted_macho(macho)

        return arch, is_encrypted
    except lief.exception as e:
        print(f"Failed to parse MachO: {e}")
        return "", False
    except Exception as e:
        print(f"An error occurred: {e}")
        return "", False


def find_arch(macho):
    if macho.header.cpu_type == lief.MachO.CPU_TYPES.ARM:
        return "ARM"
    elif macho.header.cpu_type == lief.MachO.CPU_TYPES.ARM64:
        return "ARM64"
    else:
        return "UNK"


def is_encrypted_macho(macho):
    encry_info = macho.get(lief.MachO.LOAD_COMMAND_TYPES.ENCRYPTION_INFO)
    if encry_info and encry_info.crypt_id == 1:
        return True
    encry_info_64 = macho.get(lief.MachO.LOAD_COMMAND_TYPES.ENCRYPTION_INFO_64)
    if encry_info_64 and encry_info_64.crypt_id == 1:
        return True
    return False


def read_ipa_info_and_rename(ipa_files, output_dir):
    global unique_id

    # 检查输出目录是否存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 图标存放目录
    icon_dir = os.path.join(output_dir, 'icon')
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)

    # 遍历IPA文件列表
    for ipa_path in ipa_files:
        # 提取IPA文件名 无扩展
        ipa_filename, _ = os.path.splitext(os.path.basename(ipa_path))

        # 新IPA文件名和TXT文件名
        new_ipa_name = f"{ipa_filename}_{unique_id}.ipa"
        new_ipa_path = os.path.join(output_dir, new_ipa_name)
        txt_filename = f"{unique_id}_info.txt"
        txt_path = os.path.join(output_dir, txt_filename)

        # 复制IPA文件到输出目录并重命名
        shutil.copy(ipa_path, new_ipa_path)

        # 读取IPA文件并提取Info.plist
        try:
            with zipfile.ZipFile(new_ipa_path, 'r') as ipa_zip:
                # 查找.app文件夹
                app_dirs = [name for name in ipa_zip.namelist() if name.endswith('.app/')]
                if not app_dirs:
                    raise ValueError("IPA文件中未找到.app文件夹")

                app_dir = app_dirs[0]  # 假设只有一个.app文件夹

                # 读取Info.plist的路径
                info_plist_path = os.path.join(app_dir, 'Info.plist')

                # 读取并解析Info.plist
                with ipa_zip.open(info_plist_path, 'r') as plist_file:
                    plist_content = plist_file.read()
                    info_plist = plistlib.loads(plist_content)

                # 提取信息
                bundle_identifier = info_plist.get('CFBundleIdentifier', 'Not Found')
                version = info_plist.get('CFBundleShortVersionString', 'Not Found')
                min_ios_version = info_plist.get('MinimumOSVersion', 'Not Found')

                # 写入到输出目录的文本文件中
                with open(txt_path, 'w') as output_file:
                    output_file.write(f"IPA包名: {bundle_identifier}\n")
                    output_file.write(f"版本号: {version}\n")
                    output_file.write(f"适用于iOS版本: {min_ios_version}及以上\n")

            print(f"IPA文件 {ipa_filename} 已处理，并重新命名为 {new_ipa_name}，信息已写入到 {txt_filename}")

        except Exception as e:
            print(f"处理IPA文件 {ipa_filename} 时发生错误: {e}")

            # 提取并解析 MachO 可执行文件信息
            exe_name = info_plist.get('CFBundleExecutable', 'NotFound')
            exe_path = None
            for name in ipa_zip.namelist():
                if name.endswith(f'/{exe_name}'):
                    exe_path = name
                    break

            if exe_path:
                with zipfile.ZipFile(new_ipa_path, 'r') as ipa_zip:
                    arch, is_encrypted = parse_macho_and_get_info(ipa_zip, exe_path)

                    # 写入到输出目录的文本文件中
                    with open(txt_path, 'a') as output_file:  # 使用追加模式
                        output_file.write(f"\nCPU架构: {arch}\n")
                        output_file.write(f"是否加密: {'是' if is_encrypted else '否'}\n")

                        # 提取图标
            with zipfile.ZipFile(new_ipa_path, 'r') as ipa_zip:
                app_dirs = [name for name in ipa_zip.namelist() if name.endswith('.app/')]
                if app_dirs:
                    app_dir = app_dirs[0]
                    icon_files = [name for name in ipa_zip.namelist() if
                                  name.startswith(app_dir) and any(map(name.endswith, ['.png'])) and 'AppIcon' in name]
                    for icon_file in icon_files:
                        icon_content = ipa_zip.read(icon_file)
                        icon_filename = os.path.basename(icon_file)
                        new_icon_filename = f"{unique_id}_{os.path.splitext(icon_filename)[0]}.png"
                        new_icon_path = os.path.join(icon_dir, new_icon_filename)
                        with open(new_icon_path, 'wb') as f:
                            f.write(icon_content)

        except Exception as e:
            print(f"处理IPA文件 {ipa_filename} 时发生错误: {e}")

            # 生成唯一编号 全局
            unique_id += 1

# 使用示例
ipa_files = ['1.ipa', '2.ipa']
output_dir = '文件输出路径' #运行时修改实际路径
read_ipa_info_and_rename(ipa_files, output_dir)