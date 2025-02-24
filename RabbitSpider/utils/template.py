import os
import re
import sys
import shutil
import asyncio
import argparse
from string import Template
from RabbitSpider.rabbit_execute import batch_go
from RabbitSpider.utils.control import SettingManager
from importlib.util import spec_from_file_location, module_from_spec

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
            text = Template(f.read()).substitute(project=_path, dir=_dir, spider=_file, classname='TemplateSpider')
        with open(file.replace('tmpl', 'py'), 'w', encoding='utf-8') as f:
            f.write(text)
        os.remove(file)
    if not os.path.exists(os.path.join(_path, 'spiders', _dir)):
        os.rename(os.path.abspath(os.path.join(_path, 'spiders', 'src')),
                  os.path.abspath(os.path.join(_path, 'spiders', _dir)))
    os.rename(os.path.join(_path, 'spiders', _dir, 'basic.py'),
              os.path.join(_path, 'spiders', _dir, f'{_file}.py'))
    print(f'{_path}/{_dir}/{_file}创建完成')


def runs(_dir, task_pool):
    cls_list = []
    sys.path.append(os.path.abspath('.'))
    sys.path.append(os.path.abspath('..'))
    for filename in os.listdir(os.path.join('spiders', _dir)):
        if filename.endswith('.py'):
            with open(os.path.join('spiders', _dir, filename), 'r', encoding='utf-8') as file:
                classname = re.findall(r'class\s.*?(\w+)\s*?\(\w+\)', file.read())[0]
                spec = spec_from_file_location(classname, os.path.join('spiders', _dir, filename))
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                cls_list.append(getattr(module, classname))
    asyncio.run(batch_go(cls_list, task_pool))


def cmdline():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True, help='可用的子命令')

    create_parser = subparsers.add_parser('create', help='创建一个新的爬虫项目')
    create_parser.add_argument('project', help='项目名称')
    create_parser.add_argument('dir', help='目录')
    create_parser.add_argument('spider', help='爬虫文件名')

    run_parser = subparsers.add_parser('run', help='运行一个爬虫项目')
    run_parser.add_argument('dir', help='目录')
    run_parser.add_argument('-p', '--task_pool', type=int, default=10, help='并发数')

    args = parser.parse_args()

    if args.command == 'create':
        template_to_file(f'{args.project}', _dir=f'{args.dir}', _file=f'{args.spider}')
    elif args.command == 'run':
        runs(f'{args.dir}', args.task_pool)
