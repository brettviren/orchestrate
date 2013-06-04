#!/bin/bash

# Install Python and Orchestrate from source

python_version=2.7.5
virtualenv_version=1.9.1


if [ -n "$VIRTUAL_ENV" ] ; then
    echo "Existing, virtual environment detected at $VIRTUAL_ENV"
    exit 1
fi

install_dir="$1" ; shift
temp_dir="$1" ; shift
if [ -z "$install_dir" ] ; then
    echo "usage: bootstrap.sh /path/to/venv [/path/to/temp_dir]"
    exit 1
fi

if [ -z "$temp_dir" ] ; then
    temp_dir=$(mktemp -d)
fi
if [ ! -d "$temp_dir" ] ; then
    mkdir -p "$temp_dir"
fi
log=$temp_dir/bootstrap.log
echo "Using temporary directory: $temp_dir, logging to $log" | tee $log

orch_dir="$(dirname $(dirname $(readlink -f $BASH_SOURCE)))"
source "$orch_dir/bash/orchestrate.sh"

plain_configure () {
    local where=$1 ; shift
    local prefix=$1 ; shift
    cd $where
    if [ -f config.status ] ; then
	idem "plain_configure: already configured $where"
	return
    fi
    ./configure --prefix=$prefix
}

plain_make () {
    local where="$1" ; shift
    local target="$1"; shift
    local creates="$1"; shift

    cd $where
    if [ -n "$creates" -a -f "$creates" ] ; then
	idem "plain_make: already built $creates"
	return
    fi

    make $target
}


# Idempotently install Python
mypy="$temp_dir/bin/python"
do_python () {
    python_unpacked=Python-${python_version}
    python_tarball=${python_unpacked}.tgz
    python_url="http://python.org/ftp/python/${python_version}/${python_tarball}"
    orch_download "$python_url" "$temp_dir"
    orch_unpack "$temp_dir/$python_tarball" "$temp_dir" "$python_unpacked"
    plain_configure "$temp_dir/$python_unpacked" "$temp_dir"
    plain_make "$temp_dir/$python_unpacked" "" "pybuilddir.txt"
    plain_make "$temp_dir/$python_unpacked" "install" "$mypy"
}
echo "Installing Python" | tee -a $log
do_python >> $log 2>&1

# Unless on is already activated, install virtualenv and create one,
# if needed, and activate it
do_venv () {
    myvenv="$install_dir/bin/activate"
    if [ -f $myvenv ] ; then
	idem "virtualenv already installed in $install_dir"
	return
    fi

    virtualenv_unpacked=virtualenv-${virtualenv_version}
    virtualenv_tarball=${virtualenv_unpacked}.tar.gz
    virtualenv_url="https://pypi.python.org/packages/source/v/virtualenv/${virtualenv_tarball}"
    orch_download "$virtualenv_url" "$temp_dir"
    orch_unpack "$temp_dir/$virtualenv_tarball" "$temp_dir" "$virtualenv_unpacked"
    cd $temp_dir/$virtualenv_unpacked/
    $mypy virtualenv.py --no-site-packages --distribute $install_dir
}
echo "Installing virtualenv" | tee -a $log 
do_venv >> $log 2>&1

echo "Activating virtualenv with $myvenv" | tee -a $log
source "$myvenv"		# test


do_install () {
    if [ -d "$VIRTUAL_ENV/share/orchestrate" ] ; then
	idem "orchestrate is already installed in $VIRTUAL_ENV/share/orchestrate"
	return
    fi

    cd $orch_dir
    python setup.py sdist
    pip install $(ls dist/orchestrate-*.tar.gz|tail -1)
}
echo "Installing orchestrate" | tee -a $log
do_install >> $log 2>&1

echo "You may now delete $temp_dir"
