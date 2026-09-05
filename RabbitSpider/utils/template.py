import os
import shutil
from string import Template
from RabbitSpider.utils.control import SettingManager

settings = SettingManager()


def get_template_files(path, suffix="tmpl"):
    """
    遍历目录下所有文件，生成以 tmpl 结尾的文件路径
    """
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(suffix):
                yield os.path.join(root, file)


def template_to_file(project, directory, filename):
    """
    根据模板生成项目文件
    """
    if project.lower() == 'test':
        print(f"项目名称不可以是 {project}")
        return

    template_dir = settings.get('TEMPLATE_DIR')

    # 1. 复制整个模板目录（如果项目不存在）
    if not os.path.exists(project):
        shutil.copytree(template_dir, project)

    # 2. 确保 spiders/目录存在
    spider_dir = os.path.join(project, 'spiders', directory)
    os.makedirs(spider_dir, exist_ok=True)

    # 3. 如果目标文件已存在，直接返回
    target_file = os.path.join(spider_dir, f"{filename}.py")
    if os.path.exists(target_file):
        print(f"{project}/spiders/{directory}/{filename}.py 已存在")
        return

    # 4. 如果项目已存在，复制基础模板文件
    basic_tmpl_src = os.path.join(template_dir, 'spiders', 'src', 'basic.tmpl')
    shutil.copy(basic_tmpl_src, spider_dir)

    # 5. 替换模板变量并生成 .py 文件
    for tmpl_file in get_template_files(project):
        with open(tmpl_file, 'r', encoding='utf-8') as f:
            content = Template(f.read()).substitute(project=project)
        py_file = tmpl_file.replace('.tmpl', '.py')
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(content)
        os.remove(tmpl_file)

    # 6. 如果 directory 是空的 src，重命名
    src_dir = os.path.join(project, 'spiders', 'src')
    if os.path.exists(src_dir) and not os.path.exists(spider_dir):
        os.rename(src_dir, spider_dir)

    # 7. 重命名 basic.py
    basic_py = os.path.join(spider_dir, 'basic.py')
    if os.path.exists(basic_py):
        os.rename(basic_py, target_file)

    print(f"{project}/{directory}/{filename} 创建完成")
