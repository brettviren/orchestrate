#!/usr/bin/env python
'''
A main interface to the application
'''

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
    parser.add_argument('-c', '--config', type=str, action='append',
                        help='Add a suite configuration file.')
    parser.add_argument('-s', '--shims', type=str, action='append', default=list(),
                        help='Set additional shim paths')
    parser.add_argument('-l', '--log', type=str, default='/dev/stdout',
                        help='Set a log file')
    parser.add_argument('-P', '--packages', type=str, action='append', 
                        help='Limit actions to list of packages')
    parser.add_argument('-S', '--steps', type=str, action='append', 
                        help='Limit actions to list of steps')
    parser.add_argument('suite', type=str, nargs='?',
                        help='Name the target suite')
    # Sub commands
    cmd_parsers = parser.add_subparsers()
    add_command(cmd_parsers, commands)

    return parser


def main(argv = None):
    parser = build_parser()
    opts = parser.parse_args(argv)

    logging.basicConfig(filename=opts.log, 
                        level=logging.DEBUG,
                        format='%(levelname)-7s %(asctime)-15s %(message)s (%(filename)s:%(lineno)d)')

    orch = app.Orchestrate(opts.config, opts.suite, ':'.join(opts.shims), 
                           list_split(opts.packages), list_split(opts.steps))

    # Run the command.  The command class sets the run method.
    opts.run(orch)

    return

if '__main__' == __name__:
    main()
    
