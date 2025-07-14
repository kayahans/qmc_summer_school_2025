#! /usr/bin/env python3

# Obtain the core count of the local machine (lab only)
import os
cores = os.cpu_count()
pwx_bin="pw.x"
wfc_bin="pw2qmcpack.x"
qmc_bin="qmcpack_complex"

# Import Nexus stuff
from nexus import settings,job,run_project
from nexus import generate_physical_system
from nexus import generate_pwscf
from nexus import generate_pw2qmcpack
from nexus import generate_qmcpack
from qmcpack_input import nofk,gofr

# machine settings
settings(
    pseudo_dir = './pseudos',       # Pseudopotential directory
    results    = '',                # Don't store results separately
    sleep      = 5,                 # Workflow polling frequency (sec)
    machine    = 'ws'+str(cores),   # Executing on simple workstation
    )


# Step 0.a) Specify the system to simulate
#           This test problem shows a sample workflow for
#           solids in which the DFT and wave function
#           generation is done in a primitive cell using
#           k-points to tile a supercell for subsequent
#           QMC calculations.
#
#           Here, we construct a primitive cell of carbon
#           diamond at ambient density.
#
a = 3.57
primcell  = generate_physical_system(
    units = 'A',                  # Angstrom units
    axes  = [[a/2, a/2,   0],     # Cell axes
             [  0, a/2, a/2],
             [a/2,   0, a/2]],
    elem  = ['C','C'],            # Element names
    posu  = [[0.00, 0.00, 0.00],  # Element positions (crystal units)
             [0.25, 0.25, 0.25]],
    C     = 4,                    # Pseudpotential valence charge
)


# 
# Step 0.b) Here we use Nexus to generate the optimal (most spherical)
#           supercell composed of 8 atoms (4x copies of prim. cell).
#
# 
# NB: The number of twists in the supercell determines the number of kpoint
#     needed in the primcell, so a larger supercell, or a denser twistgrid
#     are both more expensive (but still very cheap compared to QMC!)
#
tiled = primcell.structure.tile_opt(4)
tiled.add_symmetrized_kmesh(kgrid=(1,1,1),kshift=(0,0,0))
supercell = generate_physical_system(structure = tiled, C=4)

#
# Step 1.) DFT calculation with Quantum ESPRESSO
#          Note that the system we specify is the primcell
#          and a very large kpoint grid. This is done in order
#          to provide a well-converged density from which we will
#          subsequently generate SPOs to be used in the QMC calculation.
#
scf = generate_pwscf(
    identifier   = 'scf',                      # In/out file prefix
    path         = 'diamond/scf',              # Run directory
    job          = job(cores=cores,
                       app=pwx_bin),           # How to run QE
    input_type   = 'generic',                  # QE inputs below
    calculation  = 'scf',                      # SCF calculation
    input_dft    = 'pbe',                      # PBE functional
    verbosity    = 'high',                     # Show eigenvalues and occupations
    ecutwfc      = 200,                        # PW energy cutoff (Ry)
    ecutrho      = 2000,                       # Density cutoff (Ry)
    nbnd         = 8,                          # Number of SPO's to calculate
    conv_thr     = 1e-10,                      # SCF conv threshold (Ry)
    system       = primcell,                   # System to calculate
    pseudos      = ['C.ccECP.upf'],            # Pseudopotential stuff
    kgrid        = (10,10,10),                 # Dense k-point grid!
    kshift       = (0,0,0),                    # k-point grid shift
)


#
# Step 2.) DFT wave function generation with Quantum ESPRESSO
#          Notice that here we do a nscf calculation using the
#          converged density from the previous scf calculation.
#          And also the kpoints we need are given by the supercell.
#
#          If you look inside the supercell object, you'll see that it
#          knows the map from prim->super cell, and so Nexus will
#          automatically do a primcell calculation with the correct kpoints
#          to tile into the corresponding supercell.
#
nscf = generate_pwscf(
    identifier   = 'nscf',                     # In/out file prefix
    path         = 'diamond/nscf',             # Run directory
    job          = job(cores=cores,
                       app=pwx_bin),           # How to run QE
    input_type   = 'generic',                  # QE inputs below
    calculation  = 'nscf',                     # SCF calculation
    input_dft    = 'pbe',                      # PBE functional
    verbosity    = 'high',                     # Show eigenvalues and occupations
    ecutwfc      = 200,                        # PW energy cutoff (Ry)
    ecutrho      = 2000,                       # Density cutoff (Ry)
    nbnd         = 8,                          # Number of SPO's to calculate
    conv_thr     = 1e-10,                      # SCF conv threshold (Ry)
    system       = supercell,                  # System to calculate
    pseudos      = ['C.ccECP.upf'],            # Pseudopotential stuff
    dependencies = (scf,'charge_density'),
)

# Finally, convert the SPO's to hdf5 format
conv = generate_pw2qmcpack(
    identifier   = 'wfconv',
    path         = 'diamond/nscf',
    job          = job(cores=cores,
                       app=wfc_bin),
    write_psir   = False,
    dependencies = (nscf,'orbitals'),
)


#
# At this point we have a QMC wavefunction that contains all the
# kpoints necessary to tile a 2-atom prim cell into a 8-atom supercell
# with the appropriate twist grid in that supercell. Now we turn to the
# QMC portion of the workflow, which uses only the supercell object.


#
# Step 3.) VMC Jastrow optimization of 1- and 2-body Jastrows
#
# NB: For this problem a 3-body Jastrow does not noticeably
#     improve the wfn. You are encouraged to verify this!
#     [ example J3 block is provided below ]
#
optJ12 = generate_qmcpack(
    identifier      = 'diaqmc',
    path            = 'diamond/optJ12',
    job             = job(cores=cores,
                          threads=cores,
                          app=qmc_bin),
    input_type      = 'basic',
    system          = supercell,   
    twistnum        = 0,
    pseudos         = ['C.ccECP.xml'],
    J1              = True,         # Add a 1-body B-spline Jastrow
    J2              = True,         # Add a 2-body B-spline Jastrow
    J1_rcut         = 3.37,         # Cutoff for J1
    J2_rcut         = 3.37,         # Cutoff for J2
    qmc             = 'opt',        # Do a wavefunction optimization
    minmethod       = 'oneshift',   # Optimization algorithm (assumes energy minimization)
    init_cycles     = 3,            # First 4 iterations allow large parameter changes
    cycles          = 4,            # 8 subsequent iterations with smaller parameter changes
    warmupsteps     = 8,            # First 8 steps are not recorded
    blocks          = 100,          # Number of blocks to write in the .scalar.dat file
    timestep        = 0.1,          # MC step size (nothing to do with time for VMC)
    init_minwalkers = 0.01,         # Smaller values -> bigger parameter change
    minwalkers      = 0.5,          # 
    samples         = 20000,        # VMC samples per iteration
    dependencies    = (conv,'orbitals'),
)
#  Step 4.) Determine the required k-point grid size to achieve a converged
#           twist-averaged energy.  For now, we are letting Nexus construct
#           k-points in the irreducible part of the brillouin zone. 
#
#          This is broken down into similar steps as before:
#          FOR EACH nk:
#            1.) Generate an nscf wave function for all grid points in the 8 atom supercell.
#            2.) Convert the wave function to a qmcpack h5 file.
#            3.) Using the optimized jastrow from Step 3, create a "parallel" QMCPACK job
#                where we will perform VMC and DMC on a wave functions for each "twist" 
#                simultaneously.  
#            4.) Execute.
#
for nk in [1,2,3]: #each nk denotes an nk x nk x nk k-point grid.

  tiled = primcell.structure.tile_opt(4)
  tiled.add_symmetrized_kmesh(kgrid=(nk,nk,nk),kshift=(0,0,0)) #gamma centered.
  supercell = generate_physical_system(structure = tiled, C=4)

  nscfk = generate_pwscf(
    identifier   = 'nscfk',                     # In/out file prefix
    path         = 'diamond/twist_conv/n'+str(nk)+'/nscf',             # Run directory
    job          = job(cores=cores,
                       app=pwx_bin),           # How to run QE
    input_type   = 'generic',                  # QE inputs below
    calculation  = 'nscf',                     # SCF calculation
    input_dft    = 'pbe',                      # PBE functional
    verbosity    = 'high',                     # Show eigenvalues and occupations
    ecutwfc      = 200,                        # PW energy cutoff (Ry)
    ecutrho      = 2000,                       # Density cutoff (Ry)
    nbnd         = 8,                          # Number of SPO's to calculate
    conv_thr     = 1e-10,                      # SCF conv threshold (Ry)
    system       = supercell,                  # System to calculate
    pseudos      = ['C.ccECP.upf'],            # Pseudopotential stuff
    dependencies = (scf,'charge_density'),
  )

  convk = generate_pw2qmcpack(
    identifier   = 'wfconvk',
    path         = 'diamond/twist_conv/n'+str(nk)+'/nscf',
    job          = job(cores=cores,
                       app=wfc_bin),
    write_psir   = False,
    dependencies = (nscfk,'orbitals'),
  )

  qmc = generate_qmcpack(
    identifier      = 'dmc',
    path            = 'diamond/twist_conv/n' + str(nk),
    job             = job(cores=cores,
                          threads=1,
                          processes_per_node=4,
                          app=qmc_bin),
    input_type      = 'basic',
    system          = supercell,        
    pseudos         = ['C.ccECP.xml'],
    qmc             = 'dmc',
        
      # Initial VMC stuff
    vmc_warmupsteps = 8,      # Number of Equilibration steps
    vmc_blocks      = 200,    # Number of VMC blocks (To generate the DMC samples) 
    vmc_steps       = 1,      # Number of VMC steps (To generate DMC samples)
    vmc_timestep    = 0.1,    # VMC Timestep (To Generate DMC samples)
        
      # DMC stuff
    timestep        = 0.01,   # DMC timestep
    steps           = 1,      # start with small number for large timesteps [autocorrelation]
    blocks          = 300,    # Number of DMC blocks
    total_walkers   = 512,
    dependencies    = [(convk,'orbitals'),
                         (optJ12,'jastrow')],
  )
    
# Execute the workflow
run_project()
# End loop




