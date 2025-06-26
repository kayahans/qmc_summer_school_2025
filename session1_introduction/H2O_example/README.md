# Simple QMCPACK water molecule example

Calculations of the total energy by VMC and DMC for a single water
molecule. The core electrons are replaced by pseudopotentials, leaving
8 valence electrons total. The trial wavefunction is a single
determinant Slater-Jastrow wavefunction with the orbitals taken from
an HF calculation performed with GAMESS.

Run using

mpirun -n 4 qmcpack simple-H2O-vmc-dmc.xml

This calculation is expected to take under 1 minute.

Analyze using

qmca -q ev --equilibration=20 --units=ev H2O.s00*.scalar.dat

                           LocalEnergy               Variance           ratio 
H2O  series 1  -469.391489 +/- 0.113465   157.390541 +/-  6.350966   0.3353 
H2O  series 2  -469.648041 +/- 0.103980   184.381253 +/- 12.522411   0.3926 

Series 1 is the VMC calculation. Series 2 is the DMC calculation. Note
the lower energy in DMC.

Plot a trace of the block energies

qmca -t -q e --equilibration=20 --units=ev H2O.s00*.scalar.dat

Instructions on using qmca are at
https://qmcpack.readthedocs.io/en/develop/analyzing.html#qmca . qmca
can also be run without any arguments to obtain a list of options.

# Files

simple-H2O.xml - main input file.  It does VMC followed by DMC.
H2O.HF.wfs.xml - wavefunction (derived from GAMESS output)
H.BFD.xml - pseudopotential for H
O.BFD.xml - pseudopotential for O
