import os
import shutil
from string import Template
from RabbitSpider.utils.control import SettingManager

settings = SettingManager()


def tmpl_file_path(_path):
    for i in os.listdir(_path):
        if os.path.isfile(os.path.join(_path, i)):
            if i.endswith('tmpl'):
                yield os.path.join(_path, i)
        if os.path.isdir(os.path.join(_path, i)):
            for i in tmpl_file_path(os.path.join(_path, i)):
                yield i


def template_to_file(project, directory, filename):
    if project.lower() == 'test':
        print(f'项目名称不可以是{project}')
        return
    try:
        shutil.copytree(settings.get('TEMPLATE_DIR'), project)
    except FileExistsError:
        if not os.path.exists(os.path.join(project, 'spiders', directory)):
            os.mkdir(os.path.abspath(os.path.join(project, 'spiders', directory)))

        if os.path.exists(os.path.join(project, 'spiders', directory, f'{filename}.py')):
            print(f'{project}/spiders/{filename}已存在')
            return
        shutil.copy(os.path.abspath(os.path.join(settings.get('TEMPLATE_DIR'), 'spiders/src/basic.tmpl')),
                    os.path.join(project, 'spiders', directory))
    for file in tmpl_file_path(project):
        with open(file, 'r', encoding='utf-8') as f:
            text = Template(f.read()).substitute(project=project, dir=directory, spider=filename)
        with open(file.replace('tmpl', 'py'), 'w', encoding='utf-8') as f:
            f.write(text)
        os.remove(file)
    if not os.path.exists(os.path.join(project, 'spiders', directory)):
        os.rename(os.path.abspath(os.path.join(project, 'spiders', 'src')),
                  os.path.abspath(os.path.join(project, 'spiders', directory)))
    os.rename(os.path.join(project, 'spiders', directory, 'basic.py'),
              os.path.join(project, 'spiders', directory, f'{filename}.py'))
    print(f'{project}/{directory}/{filename}创建完成')
