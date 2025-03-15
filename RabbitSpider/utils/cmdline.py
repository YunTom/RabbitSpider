import argparse
from RabbitSpider.rabbit_execute import runner
from RabbitSpider.utils.template import template_to_file


def execute():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True, help='可用的子命令')

    create_parser = subparsers.add_parser('create', help='创建一个新的爬虫项目')
    create_parser.add_argument('project', help='项目名称')
    create_parser.add_argument('directory', help='目录')
    create_parser.add_argument('filename', help='爬虫文件名')

    run_parser = subparsers.add_parser('run', help='运行一个爬虫项目')
    run_parser.add_argument('directory', help='目录')
    run_parser.add_argument('-p', '--task_pool', type=int, default=10, help='并发数')
    run_parser.add_argument('-t', '--cron_expression', type=str, default='', help='crontab表达式')
    args = parser.parse_args()
    if args.command == 'create':
        template_to_file(args.project, directory=args.directory, filename=args.filename)
    elif args.command == 'run':
        runner(args.directory, args.task_pool, args.cron_expression)
