import argparse
from RabbitSpider.utils.template import template_to_file


def execute():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True, help='可用的子命令')

    create_parser = subparsers.add_parser('create', help='创建一个新的爬虫项目')
    create_parser.add_argument('project', help='项目名称')
    create_parser.add_argument('directory', help='目录')
    create_parser.add_argument('filename', help='爬虫文件名')

    args = parser.parse_args()
    if args.command == 'create':
        template_to_file(args.project, directory=args.directory, filename=args.filename)
    else:
        print('rabbit create project directory filename')
