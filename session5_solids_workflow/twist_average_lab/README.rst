Twist-Grid Convergence and Averaging
========================================
This lab is oriented around adapating workflows already present (see ``nexus/examples/qmcpack/rsqmc_quantum_espresso/``), 
but completing a VMC/DMC twist-convergence--a necessary prerequisite for many large solid-state calculations, especially those
related to equations of state.  The grid scan should be automated in the nexus script ``solids_example.py``, but what you will
do is focus on analyzing twist-averaged data. 

**Stage 1:  DFT/QMC Preliminaries (Lines 1-169)**

* This specifies the physical system (8 atom simulation cell of diamond).
* Generates the SCF wave function.
* Generates a orbitals at a single super twist (for this 8 atom cell).
* Optimizes a one and two-body jastrow.
* This represents the end of standard workflow.  The directories ``scf``, ``nscf``, and ``optJ12`` should be generated without errors.

**Stage 2:  Iterating over different twist-grids (Lines 183-241)** 

* For simplicity, this creates new physical systems with three different super twist-grids, which QMCPACK knows how to interpret as super-twists.
* It generates an appropriate NSCF set of orbitals, then goes through to do a VMC/DMC combo calculation.  
* Successful completion should give the directories ``twist_conv/n[1-3]`` without errors.  You should see ``*.s000.scalar.dat`` and ``*.s001.scalar.dat`` files.

New Features
~~~~~~~~~~~~~~~~
If you take a look inside ``twist_conv/n1``, you will find a very standard set of outputs.  ``dmc.s000.scalar.dat`` is the VMC run, and ``dmc.s001.scalar.dat``
is the DMC run.  However, let's take a look inside ``twist_conv/n2``.  The first thing to notice is that there are a LOT more files.
In particular, we have new ``dmc.g00[0-3].*`` prefixes.  For suffixes, we see our expected ``.s000.scalar.dat`` and ``.s001.scalar.dat``, 
but now we have suffixes like ``*.twist_info.dat``, ``twistnum_0.in.xml``, etc.  There are two things going on here.  

1. QMCPACK is executing multiple independent jobs in parallel.  The input file ``dmc.in`` actually lists the ``*twistnum_[0-3].in.xml``. 
Each of these files is independently runnable.  So QMCPACK puts each one of these separate executions on a different mpi rank, and labels them
with the ``dmc.g00[0-3]`` identifier.  This has nothing to do with twist-averaging, but is really convenient for it.  

2. Each ``*twistnum_[0-3].in.xml`` is an independent VMC/DMC job using a wave function corresponding to different twists.  Which twist is being
executed is given in ``<sposet_builder ... twistnum="X" ..``, where X is between 0-3.  

3. ``*.twist_info.dat`` independently outputs the twist information.  It's format is "weight kx ky kz  KX KY KZ", where the first is the
multiplicity of that twist, (kx,ky,kz) is the twist in cartesian coordiantes, and (KX,KY,KZ) are the twists in crystal coordiantes.  ``qmca``
can use this information to correctly twist-average scalar.dat files.  

Some Unusualness
~~~~~~~~~~~~~~~~~
So we attempted to specify (1x1x1), (2x2x2), and (3x3x3) grids, which should have 1, 2^3=8, and 3^3=27 twists respectively.  But for n2 and n3,
we are way short of that.  What's happening?  

Our twist-grid is symmetry aware.  We only print the symmetry inequivalent k-points--that's why ``twist_info.dat`` is telling us that some twists 
have weights other than 1.00.  You can get the total multiplicity of all the twist points by summing up the first entry in all of these files.
Try the following awk line, or manually add the numbers up yourself to see that we are actually representing the original specified grids.  

``awk 'BEGIN{sum=0}{sum+=$1}END{print sum}' *.twist_info.dat``


**Stage 3:  Analysis**

Hopefully you should understand what is being output by QMCPACK, and how that relates to the twist averaging discussion in the lecture.  
Now we just have to *do* the twist averaging for our three grids and see how the total energy changes.  While I strongly recommend you do this
manually for this workshop, QMCA does have the ability to do this for you.  

``qmca --average -q e -e 20 n*/*scalar.dat``

I ran the following on a bigger (bigger than Workshop virtual machine) and got the following:

  n1/dmc  series 0  LocalEnergy           =  -45.021611 +/- 0.003337 

  n1/dmc  series 1  LocalEnergy           =  -45.176783 +/- 0.009775 
  
  n2/dmc  series 0  LocalEnergy           =  -45.631479 +/- 0.002047 

  n2/dmc  series 1  LocalEnergy           =  -45.764559 +/- 0.008539 
   
  n3/dmc  series 0  LocalEnergy           =  -45.666595 +/- 0.001439 

  n3/dmc  series 1  LocalEnergy           =  -45.796050 +/- 0.004780 
  
  n4/dmc  series 0  LocalEnergy           =  -45.668159 +/- 0.001116 

  n4/dmc  series 1  LocalEnergy           =  -45.799752 +/- 0.007047 
  
  n6/dmc  series 0  LocalEnergy           =  -45.669764 +/- 0.000655 

  n6/dmc  series 1  LocalEnergy           =  -45.799307 +/- 0.003624 

It's OK if you don't get the exact same numbers.  We haven't fixed the seed and these calculations are extremely short.  The main
thing you should see is to within 3 sigma, this sequence is converging.  

One thing to notice in your calculations is that the error bar is in general going down for both the VMC/DMC twist-averaged runs.  
Even though all these runs are the same length, (steps, blocks, etc)., having multiple independent points drops the error like 1/sqrt(N_kpts).

Conclusions
----------------
If everything worked according to plan, you should have seen the following:

1. How we can use nexus to generate twist-grids, and how this is specified in QMCPACK xml.  

2. How to run parallel independent jobs in QMCPACK.  

3. How QMCPACK stores twist information, which is especially important for symmetry reduced twist grids.  

4. How to analyze a twist-average VMC/DMC calculation.  

5. How to determine convergence of the QMCPACK twist grids.  

Some other tidbits:

* We did not delve into it deeply, but nexus and QMCPACK support tiling primitive cells into supercells, and keeping the twist grids consistent (as discussed in lecture).

* Typically, if you establish that a certain twist grid is sufficiently converged for your calculations, you don't have to repeat the analysis for different supercell sizes.  

You can either 1.) overconverge your supercell calculations, or 2.) pick a "magic number" that is above convergence threshold but makes for easy tiling.
6x6x6 allows me to create a 1x1x1, 2x2x2, 3x3x3, and 6x6x6 supercell while keeping the k-point and twist grids absolutely consistent.

And of course, if you have questions, reach out on slack.  

