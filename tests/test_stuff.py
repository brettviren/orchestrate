#!/usr/bin/env python

def func():
    return 'foo'

def test_find_func():
    f = eval('func')
    print f, f()

class Foo(object):
    def meth(self): 
        print "I'm a method"
    def __str__(self):
        return str(dir(self.__class__))

def test_find_meth():
    f = Foo()
    print f
    m = f.__class__.__dict__['meth']
    print m
    m(f)
    

if '__main__' == __name__:
    test_find_func()
    test_find_meth()
