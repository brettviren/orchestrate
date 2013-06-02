#!/bin/bash 

# Utility functions for use by Orchestrate shim scripts


# Prepend a value to a variable.  Default delimter is ":"
# prepend <VARIABLE> <VALUE> [<delimeter>]
prepend () {
    echo $@
}    


# Append a value to a variable.  Default delimter is ":"
# append <VARIABLE> <VALUE> [<delimeter>]
append () {
    echo $@
}    


download () {
    echo $@
}
