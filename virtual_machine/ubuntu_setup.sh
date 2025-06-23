#!/bin/bash

#
# Setup script to install QMCPACK, Quantum Espresso (QE/PWSCF), PySCF
# and workshop files for QMCPACK 2025 Summer School
#
# Assumes a vanilla Ubuntu 24.04 LTS or similar
#
# Script is safely rerunnable
#
# Use configuration options below for customization
#
# Installed applications have their own unique licenses 
#
# Installs in $HOME/apps :
#
# QMCPACK and NEXUS workflow software
# Quantum ESPRESSO (QE) 7.4.1
# PySCF 2.9.0
#
# vim, emacs, xcrysden, and gnuplot are installed for convenience
#
# Getting started on a vanilla base Ubuntu:
#
# sudo apt-get -y install git
# cd $HOME
# git clone https://github.com/QMCPACK/qmc_summer_school_2025.git
# ./qmc_summer_school_2025/virtual_machine/setup_ubuntu.sh
# or
# nohup ./qmc_summer_school_2025/virtual_machinee/setup_ubuntu.sh >& out&
# tail -f out
#
# Sudoer password is needed for initial package installs and updates
# Full installation may take several hours depending on underlying hardware
#

echo -- START `date`

#
# Script configuration options
#
INSTALL_SYSTEM_PACKAGES=1
INSTALL_QMCPACK=1
INSTALL_QE=1
INSTALL_PYSCF=1
SETUP_DESKTOP=1
UPDATE_WORKSHOP_FILES=1

if [[ `lscpu` == *"aarch"* ]]; then
    echo "Running on an ARM system"
    # Potentially adjust installation for ARM systems
fi

#
# Package updates and installation
#

if  [ $INSTALL_SYSTEM_PACKAGES -eq 1 ]; then
sudo apt-get -y update
sudo apt-get -y install build-essential gcc make perl dkms # Needed for VirtualBox Guest additions
sudo apt-get -y install cmake g++ gfortran libopenmpi-dev libboost-dev libhdf5-dev libxml2-dev libfftw3-dev libopenblas-openmp-dev

sudo apt-get -y install python-is-python3 python3-pip
sudo apt-get -y install python3-numpy python3-scipy python3-matplotlib python3-pydot python3-pandas python3-h5py python3-mpi4py

# Nice to have tools
sudo apt-get -y install vim emacs-nox gnuplot xcrysden
# Cleanup
sudo apt-get -y autoremove

fi

#
# Application setup
# 
if [ ! -e $HOME/apps ]; then
    mkdir $HOME/apps
fi


#
# PySCF
#

if  [ $INSTALL_PYSCF -eq 1 ]; then

    export PYSCF_HOME=$HOME/apps/pyscf
    echo --- PYSCF_HOME set to ${PYSCF_HOME}
    if [ ! -e ${PYSCF_HOME}/pyscf/setup.py ]; then
	echo --- Downloading and installing PYSCF

	if [ -e $HOME/apps/pyscf ]; then
	    rm -r -f $HOME/apps/pyscf
	fi

	if [ ! -e $HOME/apps ]; then
	    mkdir $HOME/apps
	fi
    
       
    
	mkdir $HOME/apps/pyscf
	cd $HOME/apps/pyscf

	wget https://github.com/pyscf/pyscf/archive/refs/tags/v2.9.0.tar.gz
	tar xvzf v2.9.0.tar.gz
	rm -f v2.9.0.tar.gz
	mv pyscf-2.9.0 pyscf
	cd pyscf

	topdir=`pwd`
	here=`pwd`/opt
	herelib=`pwd`/opt/lib
	mkdir $here
	mkdir $herelib

	echo --- Top level PySCF directory `pwd`
	cd pyscf/lib
	mkdir build
	cd build
#	cmake -DBUILD_LIBCINT=0 -DBUILD_LIBXC=0 -DBUILD_XCFUN=0 -DCMAKE_INSTALL_PREFIX:PATH=$here ..
	cmake -DCMAKE_INSTALL_PREFIX:PATH=$here ..
	make -j 4

	echo --- PySCF build done
    else
	echo -- Found existing PySCF installation
    fi
# Setup PATHS so that QMCPACK cmake will detect PySCF
	export PYTHONPATH=$HOME/apps/pyscf/pyscf:$PYTHONPATH
	export LD_LIBRARY_PATH=$HOME/apps/pyscf/pyscf/opt/lib:$LD_LIBRARY_PATH
fi

# QE
if  [ $INSTALL_QE -eq 1 ]; then
    cd $HOME/apps
    if [ ! -e $HOME/apps/qe-7.4.1/bin/pw.x ]; then
	if [ ! -e q-e-qe7.4.1.tar.gz ]; then
	    wget https://gitlab.com/QEF/q-e/-/archive/qe-7.4.1/q-e-qe-7.4.1.tar.gz
	fi
	tar xvzf q-e-qe-7.4.1.tar.gz
        cd q-e-qe-7.4.1
        mkdir build_mpi
        cd build_mpi/
        cmake -DCMAKE_C_COMPILER=mpicc -DCMAKE_Fortran_COMPILER=mpif90 -DQE_ENABLE_PLUGINS=pw2qmcpack -DCMAKE_INSTALL_PREFIX=$HOME/apps/qe-7.4.1/ ..
        make -j 4
        make install

	cd ../..
	# If successfully installed we remove the whole QE directory tree and archive file
	if [ -e $HOME/apps/qe-7.4.1/bin/pw.x ]; then
	    rm -r -f $HOME/apps/q-e-qe-7.4.1.tar.gz $HOME/apps/q-e-qe-7.4.1
	fi
    fi
fi

#
# QMCPACK and patched QE setup
#
# QMCPACK files are needed for QE for pw2qmcpack.x
#
echo --- QMCPACK and QE setup
if  [ $INSTALL_QMCPACK -eq 1 ]; then
    cd $HOME/apps
    if [ ! -e qmcpack ]; then
	mkdir qmcpack
    fi
    cd qmcpack
    if [ ! -e qmcpack ]; then
	git clone https://github.com/QMCPACK/qmcpack.git --depth 1
	cd qmcpack
	# For reproducible builds, use a fixed commit or version:
	#    git checkout f95f17d2abb3cf3304553f3fd54aac3c712a1278
	#    git checkout v3.11.0
	cd ..
    else
	cd qmcpack
	git pull
	cd ..
    fi
    


    cd $HOME/apps/qmcpack
    export OMPI_MCA_rmaps_base_oversubscribe=true
	if [ $INSTALL_PYSCF -eq 1 ]; then
    	export PYTHONPATH=$HOME/apps/qmcpack/qmcpack/src/QMCTools:$PYTHONPATH
	fi

    if [ ! -e bin/qmcpack ]; then
	echo --- Building QMCPACK `date`
	if [ -e build ]; then
	    rm -r -f build
	fi
    
	mkdir build
	cd build
	cmake -DCMAKE_INSTALL_PREFIX=$HOME/apps/qmcpack -DCMAKE_CXX_COMPILER=mpiCC -DCMAKE_C_COMPILER=mpicc -DQE_BIN=$HOME/apps/qe-7.4.1/bin ../qmcpack/
	make -j 2
	make install
	#    ctest -L unit
	ctest -L deterministic --output-on-failure
	cd ..
	rm -r -f build
    fi
    
    if [ ! -e bin/qmcpack_complex ]; then
	echo --- Building QMCPACK Complex `date`
	if [ -e build_complex ]; then
	    rm -r -f build_complex
	fi
	mkdir build_complex
	cd build_complex
	cmake -DQMC_COMPLEX=1 -DCMAKE_CXX_COMPILER=mpiCC -DCMAKE_C_COMPILER=mpicc -DQE_BIN=$HOME/apps/qe-7.4.1/bin ../qmcpack/
	make -j 2
	#ctest -L unit
	ctest -L deterministic --output-on-failure
	cp -p bin/qmcpack_complex $HOME/apps/qmcpack/bin
	#    cd ../build/bin
	#    ln -sf ../../build_complex/bin/qmcpack_complex qmcpack_complex
	cd ..
	rm -r -f build_complex
	cd ..
    fi

fi


cd $HOME
echo --- Shell setup `date`
cp -p .bashrc .bashrc_safe
HAVESETUP=`grep -c START-QMCPACK-RELATED $HOME/.bashrc`
if  [ $HAVESETUP -eq 0 ]; then
    echo --- No existing .bashrc entries
cat >>$HOME/.bashrc <<EOF
# START-QMCPACK-RELATED
# END-QMCPACK-RELATED
EOF
fi
echo --- Updating .bashrc entries
cat >__insert_this<<EOF
# QMCPACK and NEXUS
export PATH=\$HOME/apps/qmcpack/bin:\$PATH
export PATH=\$HOME/apps/qmcpack/qmcpack/nexus/bin:\$PATH
export PYTHONPATH=\$HOME/apps/qmcpack/qmcpack/nexus/lib:\$PYTHONPATH
export PYTHONPATH=\$HOME/apps/qmcpack/qmcpack/utils/afqmctools:\$PYTHONPATH
# QE
export PATH=\$HOME/apps/qe-7.4.1/bin:\$PATH
# PySCF
export PYTHONPATH=\$HOME/apps/pyscf/pyscf:\$PYTHONPATH
export PYTHONPATH=\$HOME/apps/qmcpack/qmcpack/src/QMCTools:\$PYTHONPATH
export LD_LIBRARY_PATH=\$HOME/apps/pyscf/pyscf/opt/lib:\$LD_LIBRARY_PATH
# Default threads
export OMP_NUM_THREADS=1
EOF
lead='^# START-QMCPACK-RELATED'
tail='^# END-QMCPACK-RELATED'
output=$(sed -e "/$lead/,/$tail/{ /$lead/{p; r __insert_this
        }; /$tail/p; d }" .bashrc)
echo "$output" >.bashrc
rm -f __insert_this


# Add setup info to current shell for convenience
# QMCPACK and NEXUS
export PATH=$HOME/apps/qmcpack/bin:$PATH
export PATH=$HOME/apps/qmcpack/qmcpack/nexus/bin:$PATH
export PYTHONPATH=$HOME/apps/qmcpack/qmcpack/nexus/lib:$PYTHONPATH
# QE
export PATH=$HOME/apps/qe-7.4.1/bin:$PATH
# PySCF
export PYTHONPATH=$HOME/apps/pyscf/pyscf:$PYTHONPATH
export PYTHONPATH=$HOME/apps/qmcpack/qmcpack/src/QMCTools:$PYTHONPATH
export LD_LIBRARY_PATH=$HOME/apps/pyscf/pyscf/opt/lib:$LD_LIBRARY_PATH

export OMP_NUM_THREADS=1

if  [ $SETUP_DESKTOP -eq 1 ]; then

echo -- Ubuntu Desktop convenience
if [ ! -e $HOME/.config/autostart/gnome-terminal-desktop ]; then

    if [ ! -e $HOME/.config ]; then
	mkdir $HOME/.config
    fi
    if [ ! -e $HOME/.config/autostart ]; then
	mkdir $HOME/.config/autostart
    fi
    
cat >$HOME/.config/autostart/gnome-terminal.desktop<<EOF
[Desktop Entry]
Type=Application
Exec=gnome-terminal
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[en_US]=Terminal
Name=Terminal
Comment[en_US]=
Comment=
EOF
echo "Added startup Terminal"
fi
if [ ! -e $HOME/Desktop/WORKSHOP_README.txt ]; then
    if [ ! -e $HOME/Desktop ]; then
	mkdir $HOME/Desktop
    fi
    cat >$HOME/Desktop/WORKSHOP_README.txt<<EOF
QMC Virtual Summer School 2025 Virtual Machine based on Ubuntu 24.04 LTS

https://qmcpack.org/qmc2025

https://github.com/QMCPACK/qmc_summer_school_2025

This image contains installed versions of

QMCPACK
NEXUS
Quantum ESPRESSO (QE) 7.4.1
PySCF 2.9.0

See the individual packages for details of their specific open-source licenses.

For visualization xcrysden is available, and for editing vim and emacs are already installed.

Programs are installed in \$HOME/apps configured to be available on the \$PATH , e.g., "pw.x".

Install additional packages from the Ubuntu registry e.g. sudo apt-get install package_name

To update the workshop files:

cd \$HOME/qmc_summer_school_2025
git pull

To update the QMCPACK and NEXUS sources:

cd \$HOME/apps/qmcpack/qmcpack
git pull
EOF
echo "Added Desktop WORKSHOP_README.txt"
fi
fi

if  [ $UPDATE_WORKSHOP_FILES -eq 1 ]; then
echo --- Workshop files `date`
# In case the install script was copied in vs run the workshop git
# setup, otherwise update
cd $HOME
if [ ! -e qmc_summer_school_2025 ]; then
    git clone https://github.com/QMCPACK/qmc_summer_school_2025.git
else
    cd qmc_summer_school_2025
    git pull
    cd ..
fi
fi
echo -- END `date`

