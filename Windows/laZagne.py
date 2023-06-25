import argparse
import logging
import os
import sys
import time

from lazagne.config.constant import constant
from lazagne.config.manage_modules import get_categories
from lazagne.config.run import run_lazagne, create_module_dic
from lazagne.config.write_output import write_in_file, StandardOutput

constant.st = StandardOutput()  # Object used to manage the output / write functions (cf write_output file)
modules = create_module_dic()


def configure_output(output_dir=None, txt_format=False, json_format=False, all_format=False):
    if output_dir:
        if os.path.isdir(output_dir):
            constant.folder_name = output_dir
        else:
            print('[!] Specify a directory, not a file !')

    if txt_format:
        constant.output = 'txt'

    if json_format:
        constant.output = 'json'

    if all_format:
        constant.output = 'all'

    if constant.output:
        if not os.path.exists(constant.folder_name):
            os.makedirs(constant.folder_name)
            # constant.file_name_results = 'credentials' # let the choice of the name to the user

        if constant.output != 'json':
            constant.st.write_header()


def configure_quiet_mode(is_quiet_mode=False):
    if is_quiet_mode:
        constant.quiet_mode = True


def configure_verbosity(verbose=0):
    if verbose == 0:
        level = logging.CRITICAL
    elif verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    formatter = logging.Formatter(fmt='%(message)s')
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    # If other logging handlers are set
    for r in root.handlers:
        r.setLevel(logging.CRITICAL)
    root.addHandler(stream)


def configure_advanced_options(user_password=None):
    if user_password:
        constant.user_password = user_password


def run_lazagne_module(category_selected='all', subcategories=None, password=None):
    """
    This function will be removed, still there for compatibility with other tools
    Everything is on the config/run.py file
    """
    for pwd_dic in run_lazagne(category_selected=category_selected, subcategories=subcategories, password=password):
        yield pwd_dic


def clean_args(arg):
    """
    Remove unnecessary values to get only subcategories
    """
    keys_to_remove = [
        'output', 'write_normal', 'write_json', 'write_all', 'verbose', 'auditType', 'quiet'
    ]
    for key in keys_to_remove:
        arg.pop(key, None)
    return arg


def parse_arguments():
    parser = argparse.ArgumentParser(description=constant.st.banner, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-version', action='version', version='Version ' + str(constant.CURRENT_VERSION),
                        help='laZagne version')

    # ------------------------------------------- Permanent options -------------------------------------------
    # Version and verbosity
    parser.add_argument('-v', dest='verbose', action='count', default=0, help='increase verbosity level')
    parser.add_argument('-quiet', dest='quiet', action='store_true', default=False,
                        help='quiet mode: nothing is printed to the output')

    # Output
    parser.add_argument('-oN', dest='write_normal', action='store_true', default=None,
                        help='output file in a readable format')
    parser.add_argument('-oJ', dest='write_json', action='store_true', default=None,
                        help='output file in a json format')
    parser.add_argument('-oA', dest='write_all', action='store_true', default=None, help='output file in both formats')
    parser.add_argument('-output', dest='output', action='store', default='.',
                        help='destination path to store results (default:.)')

    # Windows user password
    parser.add_argument('-password', dest='password', action='store', help='Windows user password')

    # Add options and suboptions to all modules
    all_categories = get_categories()
    for c in all_categories:
        category_parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=constant.max_help)
        )
        category_parser._optionals.title = all_categories[c]['help']

        # Manage options
        for module in modules[c]:
            m = modules[c][module]
            category_parser.add_argument(
                m.options['command'], action=m.options['action'], dest=m.options['dest'], help=m.options['help']
            )

            # Manage all suboptions by modules
            if m.suboptions and m.name != 'thunderbird':
                for sub in m.suboptions:
                    subparser = argparse.ArgumentParser(
                        add_help=False,
                        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=constant.max_help)
                    )
                    subparser._optionals.title = sub['title']
                    if 'type' in sub:
                        subparser.add_argument(
                            sub['command'], type=sub['type'], action=sub['action'], dest=sub['dest'],
                            help=sub['help']
                        )
                    else:
                        subparser.add_argument(
                            sub['command'], action=sub['action'], dest=sub['dest'], help=sub['help']
                        )
                    category_parser.add_argument(subparser)

    # Main commands
    subparsers = parser.add_subparsers(help='Choose a main command')
    subparsers.required = True
    subparsers.dest = 'auditType'

    subparsers.add_parser('all', parents=[parser], help='Run all modules')
    for c in all_categories:
        subparser = subparsers.add_parser(c, parents=[parser], help='Run {} module'.format(c))
        subparser.set_defaults(auditType=c)

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Define constant variables
    configure_output(
        output_dir=args.output,
        txt_format=args.write_normal,
        json_format=args.write_json,
        all_format=args.write_all
    )
    configure_verbosity(verbose=args.verbose)
    configure_advanced_options(user_password=args.password)
    configure_quiet_mode(is_quiet_mode=args.quiet)

    # Print the title
    constant.st.first_title()

    start_time = time.time()

    category = args.auditType
    subcategories = clean_args(vars(args))

    for result in run_lazagne(category_selected=category, subcategories=subcategories, password=args.password):
        pass

    write_in_file(constant.stdout_result)
    constant.st.print_footer(elapsed_time=str(time.time() - start_time))


if __name__ == '__main__':
    main()
