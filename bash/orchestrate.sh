#!/bin/bash 

# Utility functions for use by Orchestrate shim scripts


msg () {
    echo "$@"
}
idem () {
    msg "IDEM: $@"
}
fail () {
    msg "FAILURE: $@"
    exit 1
}

runcmd () {
    echo "Running: $@ in $(pwd)"
    $@
    err=$?
    if [ "$err" != "0" ] ; then
	exit $err
    fi
    return 0
}
goto () {
    runcmd pushd $@ > /dev/null 2>&1
}
goback () {
    popd > /dev/null 2>&1
}

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


## Download a file from a <URL> (default is package_url) to an optionally specified <targetdir> (default is source_dir)
## orch_download [<URL>] [<targetdir>]
orch_download () {
    local url=$1 ; shift
    local targetdir=$1 ; shift

    if [ -z "$url" ] ; then
	url="$ORCH_PACKAGE_URL"
    fi

    if [ -z "$targetdir" ] ; then
	targetdir="$ORCH_SOURCE_DIR"
    fi
    if [ ! -d "$targetdir" ] ; then
	runcmd mkdir -p $targetdir
    fi

    local target="$targetdir/$(basename $url)"
    if [ -f "$target" ] ; then
	idem "download: target exists: $target"
	return 0
    fi

    local cmd

    # try wget
    cmd=$(type -P -f wget)
    if [ -n "$cmd" ] ; then
	runcmd $cmd --no-check-certificate -O $target $url
	return $?
    fi

    # try curl
    cmd=$(type -P -f curl)
    if [ -n "$cmd" ] ; then
	runcmd $cmd -o $target $url
	return $?
    fi

    fail "No downloader found"
}

## unpack <archive> to <where> creating <creates>
## defaults: 
##   archive: $ORCH_SOURCE_DIR/$(basename $ORCH_PACKAGE_URL)
##   where: $ORCH_SOURCE_DIR
##   creates: $ORCH_UNPACKED_DIR
## orch_unpack <archive> [<where>] [<creates>]
orch_unpack () {
    local what=$1 ; shift       # the archive file to unpack
    local where=$1 ; shift      # directory in which to unpack
    local creates=$1 ; shift    # something that the unpacking creates

    if [ -z "$what" ] ; then
	what="$ORCH_SOURCE_DIR/$(basename $ORCH_PACKAGE_URL)"
    fi
    if [ -z "$where" ] ; then
	where=$ORCH_SOURCE_DIR
    fi
    if [ -z "$creates" ] ; then
	creates=$ORCH_UNPACKED_DIR
    fi

    goto $where

    if [ -d "$creates" -o -f "$creates" ] ; then
        idem "unpack: output directory for $what already exists: $creates"
        return
    fi

    if [ -n "$(echo $what | egrep '\.zip$')" ] ; then
	runcmd unzip $what
    elif [ -n "$(echo $what | egrep '\.tar.gz|.tgz$')" ] ; then
	runcmd tar xzf $what
    elif [ -n "$(echo $what | egrep '.tar.bz2|.tbz|.tbz2')" ] ; then
        runcmd tar xjf $what
    elif [ -n "$(echo $what | egrep '.tar')" ] ; then
        runcmd tar xf $what
    else
        fail "do not know how to unpack $what"
    fi

    if [ -d "$creates" -o -f "$creates" ] ; then return ; fi

    goback

    fail "Failed to unpack $what to $creates in $where"
}

## run autoconf configure from the unpacked dir with prefix to the install dir
## any extra arguments are simply passed to configure.
## orch_configure [<addtional args>]
orch_configure () {
    if [ -f config.status ] ; then
	idem "configure: already run in $(pwd)"
	return
    fi
    $ORCH_UNPACKED_DIR/configure --prefix $ORCH_INSTALL_DIR "$@"
}


## Run make
## orch_make [<target>] [<creates>]
orch_make () {
    target=$1 ; shift
    creates=$1 ; shift

    if [ -n "$creates" -a -f "$creates" ] ; then
	idem "make: already created $creates"
	return
    fi

    runcmd make $target
}
