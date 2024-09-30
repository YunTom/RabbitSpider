import os
import shutil
import argparse
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


def template_to_file(_path, _dir, _file):
    if _path.lower() == 'test':
        print(f'项目名称不可以是{_path}')
        return
    try:
        shutil.copytree(settings.get('TEMPLATE_DIR'), _path)
    except FileExistsError:
        if not os.path.exists(os.path.join(_path, 'spiders', _dir)):
            os.mkdir(os.path.abspath(os.path.join(_path, 'spiders', _dir)))

        if os.path.exists(os.path.join(_path, 'spiders', _dir, f'{_file}.py')):
            print(f'{_path}/spiders/{_file}已存在')
            return
        shutil.copy(os.path.abspath(os.path.join(settings.get('TEMPLATE_DIR'), 'spiders/src/basic.tmpl')),
                    os.path.join(_path, 'spiders', _dir))
    for file in tmpl_file_path(_path):
        with open(file, 'r', encoding='utf-8') as f:
            text = Template(f.read()).substitute(bot_dir=os.path.abspath(f'./{_path}'), project=_path, dir=_dir,
                                                 spider=_file, classname=_file.capitalize())
        with open(file.replace('tmpl', 'py'), 'w', encoding='utf-8') as f:
            f.write(text)
        os.remove(file)
    if not os.path.exists(os.path.join(_path, 'spiders', _dir)):
        os.rename(os.path.abspath(os.path.join(_path, 'spiders', 'src')),
                  os.path.abspath(os.path.join(_path, 'spiders', _dir)))
    os.rename(os.path.join(_path, 'spiders', _dir, 'basic.py'),
              os.path.join(_path, 'spiders', _dir, f'{_file}.py'))
    print(f'{_path}/{_dir}/{_file}创建完成')


def create_project():
    parser = argparse.ArgumentParser()
    parser.add_argument('create', default='create', help='参数：create')
    parser.add_argument('project', help='参数：项目名称')
    parser.add_argument('dir', help='参数：目录')
    parser.add_argument('spider', help='参数：文件名称')
    args = parser.parse_args()
    template_to_file(f'{args.project}', _dir=f'{args.dir}', _file=f'{args.spider}')
