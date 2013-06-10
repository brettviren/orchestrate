#!/usr/bin/env python
'''
A main interface to the application
'''

import sys
import argparse
import logging

import commands, app

from util import list_split

# Note, the patterns governing how argparse subcommands are done here
# and in commands.py are taken from the cobe IRC bot.
def add_command(parsers, submodule):
    for name in dir(submodule):
        obj = getattr(submodule, name)
        if hasattr(obj, "add_subparser"):
            obj.add_subparser(parsers)
    return


def build_parser():
    'Build command line parser'

    parser = argparse.ArgumentParser(description = 'Orchestrate a Suite Installation')

    # Global options
    parser.add_argument('-c', '--config', type=str, action='append', required=True,
                        help='Add a suite configuration file.')
    parser.add_argument('-s', '--shims', type=str, action='append', default=list(),
                        help='Set additional shim paths')
    parser.add_argument('-l', '--log', type=str, default='/dev/stdout',
                        help='Set a log file')
    parser.add_argument('-P', '--packages', type=str, action='append', 
                        help='Limit actions to list of packages')
    parser.add_argument('--last-package', type=str, default=None,
                        help='Stop after acting on given package')
    parser.add_argument('-S', '--steps', type=str, action='append', 
                        help='Limit actions to list of steps')
    parser.add_argument('--last-step', type=str, default=None,
                        help='Stop after performing given step')
    parser.add_argument('--top-loop', choices=['step','steps','package','packages'],
                        default = 'packages',
                        help = 'Top loop on steps or packages')
    parser.add_argument('suite', type=str, nargs='?',
                        help='Name the target suite')

    # Sub commands
    cmd_parsers = parser.add_subparsers()
    add_command(cmd_parsers, commands)

    return parser


def truncate_list(lst, stop_at):
    if not stop_at:
        return lst
    return lst[:lst.index(stop_at)+1]


def app_main(args):
    '''
    The main interface provides access to the orchestrate application.
    '''

    parser = build_parser()
    opts = parser.parse_args(args)

    logging.basicConfig(filename=opts.log, 
                        level=logging.DEBUG,
                        format='%(levelname)-7s %(message)s (%(filename)s:%(lineno)d)')

    orch = app.Orchestrate(opts.config, opts.suite, ':'.join(opts.shims), 
                           list_split(opts.packages), list_split(opts.steps))
    orch.set_iter_dominance(opts.top_loop)
    steps = truncate_list(orch.steps, opts.last_step)
    packages = truncate_list(orch.packages, opts.last_package)
    orch.set_shims(packages, steps)

    # Run the command.  The command class sets the run method.
    opts.run(orch)

    return

def main(argv = None):
    if not argv:
        argv = sys.argv
    args = argv[1:]
    app_main(args)

if '__main__' == __name__:
    main()
    
