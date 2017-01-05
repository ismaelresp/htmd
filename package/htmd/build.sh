#!/usr/bin/env bash
# (c) 2015-2016 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#

echo "building"

export PATH=$PATH:/usr/bin/:/bin/
printenv

# Compile any C code

if [ "$CC" == "x86_64-w64-mingw32-g++" ]; then
	OSNAME=Windows
fi

T="$PWD"
for S in "$PWD/htmdlib/"* "$PWD/C/"*; do
  echo "=== Compiling $S ==="
	cd "$S"
  FLAGS=""
  if [ "$OSNAME" == "Darwin" ]; then
   FLAGS=-Wl,-headerpad_max_install_names 
  fi
	make CPURE=$CPURE CC=$CC FC=$FC STATIC=$STATIC PLATFORM=$OSNAME TYPE=$TYPE EXTRAFLAGS=$FLAGS
	cd "$T"
done

find htmd -type d -name __pycache__ -exec rm -rf {} \; -print || true

echo "Installing into $PREFIX"

	DIR="$SP_DIR"

	if [ "$DIR" != "" ]; then
		mkdir -p "$DIR"
	fi
	if [ -e "$DIR" ]; then
		pwd
		ls
		cp -r htmd  $DIR/
		cp -r htmdx  $DIR/
		rm -rf $(find "$DIR" -name .git -type d) 
    rm -rf $DIR/htmd/data
	  rm -rf $DIR/htmd/.idea
	  rm -rf $DIR/htmdx/.idea
    rm -rf $DIR/htmd/.ipynb_checkpoints
    rm -rf $DIR/htmd/Untitled*


    echo "def version():" > $DIR/htmd/version.py
    echo "    return \"$PKG_VERSION\"" >> $DIR/htmd/version.py

	else
		echo "Error: PREFIX not defined"
		exit 1
	fi

cd "$DIR/../../"

chmod -R a+rX "$PREFIX"



# Try this to hopefully suppess travis build error on osx "shell_session_update"# cf https://github.com/travis-ci/travis-ci/issues/6522 
set +e
echo $PATH
echo PATH=$PWD:$PATH
echo "#!/bin/sh
exit 0
" > shell_session_update
chmod +x shell_session_update
exit 0
