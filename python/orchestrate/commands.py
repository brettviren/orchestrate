#!/usr/bin/env python
'''
Command classes driving a particular facet of the app.
'''

# http://stackoverflow.com/questions/8368110/python-argparse-subcommand-subcommand

class CommandProtocol(object):
    '''
    A (sub) command to a main program implements this pattern.
    '''
    @classmethod
    def add_subparser(cls, parser):
        '''
        Create a argparse parser for any command options.
        '''
        return

    @staticmethod
    def run(app):
        '''
        Run the command on the application.
        '''
        return


class ListCommand(object):
    '''
    A command to list things about the suite.
    '''
    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser('list', help='List the contents of the suite')
        subparser.set_defaults(run = cls.run)
        return

    @staticmethod
    def run(app):
        '''
        Run the command on the application
        '''
        for s in app.shims:
            print '{package}/{version} using:'.format(**s.vars)
            for step in s.steps:
                s.get_runner(step) # trigger dep_setup to be filed
                print '\t%s: %s' % (step, s.shim_scripts[step])
            for dep in s.dep_setup:
                print '\tdep: %s' % str(dep)

        return
