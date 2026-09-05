import argparse

from RabbitSpider.utils.template import template_to_file


def execute() -> None:
    parser = argparse.ArgumentParser(
        prog="rabbit",
        description="RabbitSpider 命令行工具",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    create_parser = subparsers.add_parser(
        "create",
        help="创建一个新的爬虫项目",
    )
    create_parser.add_argument(
        "project",
        help="项目名称",
    )
    create_parser.add_argument(
        "directory",
        help="项目目录",
    )
    create_parser.add_argument(
        "filename",
        help="爬虫文件名",
    )

    args = parser.parse_args()

    if args.command == "create":
        template_to_file(
            project=args.project,
            directory=args.directory,
            filename=args.filename,
        )
