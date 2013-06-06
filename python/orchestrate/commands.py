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
                print '\t%s: %s' % (step, s.shim_scripts[step])
            for dep in s.dep_ver:
                print '\tdep: %s' % str(dep)

        return

class CheckCommand(object):
    '''
    A command to check the configuration.
    '''
    @classmethod
    def add_subparser(cls, parser):
        subparser = parser.add_parser('check', help='Check the suite configuration file')
        subparser.set_defaults(run = cls.run)
        return

    @staticmethod
    def run(app):
        '''
        Run the command on the application
        '''
        for s in app.shims:
            print '%s/%s:' % (s.vars['package_name'], s.vars['package_version'])
            for k,v in sorted(s.vars.items()):
                if k in ['package_name','package','package_version','version']:
                    continue
                print '\t%s = %s' % (k,v)
        return

