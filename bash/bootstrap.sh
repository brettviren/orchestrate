#!/bin/bash

# orchestrate requires some Python facilities not found on lame distributions
#
# A non-paleolithic version of Python
# Some modules not always provided by the system:
# - pkg_resources
#
# To help the installer target systems which can not satisfy these
# requirements, this script will install a recent Python and
# virtualenv.  It will create a virtual env and populate it with extra
# modules.

python_version=2.7.5
virtualenv_version=1.9.1

top_dir="$(dirname $(dirname $(readlink -f $BASH_SOURCE)))"
cd $top_dir
echo "Top at $top_dir"

source "$top_dir/bash/orchestrate.sh"

bootstrap_dir="$top_dir/bootstrap"
echo "bootstrap in $bootstrap_dir"

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

mypy="$bootstrap_dir/bin/python"
myvenv="$bootstrap_dir/venv"

# Idempotently install Python
python_unpacked=Python-${python_version}
python_tarball=${python_unpacked}.tgz
python_url="http://python.org/ftp/python/${python_version}/${python_tarball}"
orch_download "$python_url" "$bootstrap_dir"
orch_unpack "$python_tarball" "$bootstrap_dir" "$python_unpacked"
plain_configure "$bootstrap_dir/$python_unpacked" "$bootstrap_dir"
plain_make "$bootstrap_dir/$python_unpacked" "" "pybuilddir.txt"
plain_make "$bootstrap_dir/$python_unpacked" "install" "$mypy"


# Unless on is already activated, install virtualenv and create one,
# if needed, and activate it
if [ -z "$VIRTUAL_ENV" ] ; then
    if [ ! -d $myvenv ] ; then
	virtualenv_unpacked=virtualenv-${virtualenv_version}
	virtualenv_tarball=${virtualenv_unpacked}.tar.gz
	virtualenv_url="https://pypi.python.org/packages/source/v/virtualenv/${virtualenv_tarball}"
	orch_download "$virtualenv_url" "$bootstrap_dir"
	orch_unpack "$virtualenv_tarball" "$bootstrap_dir" "$virtualenv_unpacked"
	cd $bootstrap_dir/$virtualenv_unpacked/
	$mypy virtualenv.py --distribute $myvenv
    fi
    source "$myvenv/bin/activate"
fi

