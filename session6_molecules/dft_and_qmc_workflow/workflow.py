#! /usr/bin/env python3

import os
import shutil

# Nexus setup
from nexus import settings,job,run_project,obj
from nexus import generate_physical_system
from nexus import ppset
from nexus import generate_qmcpack
from nexus import generate_pyscf
from nexus import generate_convert4qmc
from nexus import loop,linear,vmc,dmc
from nexus import get_machine

# machine and run settings
calc_cores = 64
qmc_bin="qmcpack"
settings(
    pseudo_dir = './pseudopotentials',  # Pseudopotential directory
    generate_only = 0,                  # only write input files, T/F
    results    = '',                    # Don't store results separately
    sleep      = 120,                   # Workflow polling frequency (sec)
#    machine    = 'ws'+str(calc_cores),   # Executing on simple workstation
    machine = 'baseline',               # a cluster with queuing system
    account = 'MAT269',                 # required account name in submitted jobs
    )

ourmachine=get_machine('baseline')
ourmachine.queue_size=24                # limit number of submitted jobs

pyscf_job = job(nodes=1,threads=32,hours=1,serial=True)
conv_job = job(nodes=1,threads=1,hours=1)
opt_job = job(nodes=1,cores=64, threads=1, hours=24, app=qmc_bin)
vmc_job = job(nodes=1,cores=64, threads=1, hours=24, app=qmc_bin)
dmc_job = job(nodes=1,cores=64, threads=1, hours=24, app=qmc_bin)

ppset(
    label   = 'ccecp',
    qmcpack = ['P.ccECP.xml', 'C.ccECP.xml', 'F.ccECP.xml', 'H.ccECP.xml', 'N.ccECP.xml', 'S.ccECP.xml', 'O.ccECP.xml'],
    )

atom_values = {
    'F': 7,
    'O': 6,
    'N': 5,
    'C': 4,
    'H': 1,
    'S': 6,
    'P': 5
}

functionals_for_dft_runs = [ 'LDA', 'PBE0-D4', 'PBE0', 'PBE', 'R2SCAN', 'B3LYP', 'WB97M-V' ]
functionals_for_qmc_runs = [ 'LDA', 'PBE0', 'PBE', 'R2SCAN', 'B3LYP',  'WB97M-V' ]

directory = 'structures'
for struct in os.listdir(directory):
    Mysystem, geom = os.path.splitext(struct)

    # Initialize an empty dictionary to store atoms found in the xyz file
    atoms_in_file = {}

    # Construct the full file path
    filepath = os.path.join(directory, struct)

    # Read the file and check for atoms
    with open(filepath, 'r') as file:
        next(file)  # Skip the first line of xyz file
        next(file)  # Skip the secone line of xyz file
        for line in file:
            atom_type = line.split()[0]
            if atom_type in atom_values:
                atoms_in_file[atom_type] = atom_values[atom_type]

    # Generate the physical system using the atoms found
    system = generate_physical_system(structure=filepath, **atoms_in_file)

    for dftfunc in functionals_for_dft_runs:
        # perform DFT 
        scf = generate_pyscf(
            identifier = Mysystem,                      # log output goes to scf.out
            path       = Mysystem+'/'+dftfunc+'/SCF',   # directory to run in
            job        = pyscf_job,
            system     = system,
            mole       = obj(                           # used to make Mole() inputs
                basis    = 'ccecp-ccpvqz', 
                ecp      = 'ccecp',
                symmetry = False,
                spin     = 0,                           # Singlet state (Enter S in 2S+1) 
                verbose  = 5,
                ),
            calculation = obj(
                method      = 'ROKS',                   # Restricted Orbital Kohn Sham
                df_fitting  = True,                     # Density fitting
                max_cycle   = 200,                      # Max SCF cycles
                level_shift = 0.0,                      # Mixing orbitals for convergence
                tol         = '1e-10',                  # Accuracy needed for convergence
                xc          = dftfunc,                  # Exchange and correlation functional                                     
                ),                                     
            save_qmc   = True ,                         # Save the orbital to QMCPACK format
            )


        if dftfunc in functionals_for_qmc_runs:

            # convert orbitals to QMCPACK format
            c4q = generate_convert4qmc(
                identifier   = 'c4q',
                path         = Mysystem+'/'+dftfunc+'/SCF',   # directory to run in
                job          = conv_job,
                dependencies = (scf,'orbitals'),              # Create a dependency to DFT success
                )

            # collect dependencies relating to orbitals
            orbdeps = [(c4q,'particles'),                     # PySCF changes particle positions
                 (c4q,'orbitals' )]

            # run VMC determinant only with QMCPACK. Sanity check / benchmark timings
            qmc_hf = generate_qmcpack(
                identifier   = 'vmc_det_only',
                path         = Mysystem+'/'+dftfunc+'/vmc_det_only',
                job          = vmc_job,
                system       = system,
                pseudos      = 'ccecp',
                jastrows     = [],
                qmc          = 'vmc',
                warmupsteps  = 1000,
                blocks       = 100,
                steps        = max(int(48000/calc_cores),1),
                substeps     = 3,
                timestep     = 0.5,
                dependencies = orbdeps,
            )


            # add+optimize 2-body Jastrow
            optJ2_1 = generate_qmcpack(
                identifier        = 'opt_J2_1',
                path              = Mysystem+'/'+dftfunc+'/opt_J2_1',
                job               = opt_job,
                system            = system,
                pseudos           = 'ccecp',
                J2                = True,         # 2-body B-spline Jastrow
                J1_rcut           = 4.0,          # 4 Bohr cutoff for J1
                J2_rcut           = 7.0,          # 7 Bohr cutoff for J2
                qmc               = 'opt',        # quartic variance optimization
                cycles            = 6,            # loop max of 6
                alloweddifference = 1e-3,         # increase allowed energy difference
                samples           = 96000,
                substeps          = 3,
                timestep          = 0.5,
                blocks            = 10,
                warmupsteps       = 1000,
                dependencies      = orbdeps,
            )

            # run VMC with J2 results
            qmc_vmc_J2_1 = generate_qmcpack(
                identifier   = 'vmc_J2_1',
                path         = Mysystem+'/'+dftfunc+'/vmc_J2_1',
                job          = vmc_job,
                system       = system,
                jastrows     = [],
                pseudos      = 'ccecp',
                qmc          = 'vmc',
                warmupsteps  = 1000,
                blocks       = 100,
                steps        = max(int(48000/calc_cores),1),
                substeps     = 3,
                timestep     = 0.5,
                dependencies = orbdeps+[(optJ2_1,'jastrow')],
            )

            # further optimize 2-body Jastrow
            optJ2_2 = generate_qmcpack(
                identifier        = 'opt_J2_2',
                path              = Mysystem+'/'+dftfunc+'/opt_J2_2',
                job               = opt_job,
                system            = system,
                jastrows          = [],
                pseudos           = 'ccecp',
                qmc               = 'opt',        # quartic variance optimization
                cycles            = 6,            # loop max of 6
                alloweddifference = 1e-3,         # increase allowed energy difference
                samples           = 384000,
                substeps          = 3,
                timestep          = 0.5,
                blocks            = 10,
                warmupsteps       = 1000,
                dependencies      = orbdeps+[(optJ2_1,'jastrow')],
            )


            # run VMC with J2_2 results
            qmc_vmc_J2_2 = generate_qmcpack(
                identifier   = 'vmc_J2_2',
                path         = Mysystem+'/'+dftfunc+'/vmc_J2_2',
                job          = vmc_job,
                system       = system,
                jastrows     = [],
                pseudos      = 'ccecp',
                qmc          = 'vmc',
                warmupsteps  = 1000,
                blocks       = 100,
                steps        = max(int(48000/calc_cores),1),
                substeps     = 3,
                timestep     = 0.5,
                dependencies = orbdeps+[(optJ2_2,'jastrow')],
            )

            
            # add+optimize 3-body Jastrow
            optJ3_1 = generate_qmcpack(
                identifier        = 'opt_J3_1',
                path              = Mysystem+'/'+dftfunc+'/opt_J3_1',
                job               = opt_job,
                system            = system,
                pseudos           = 'ccecp',
                J3                = True,         # 3-body poly Jastrow
                J3_rcut           = 5,
                qmc               = 'opt',        # quartic variance optimization
                cycles            = 10,           # loop max of 10
                alloweddifference = 1e-3,         # increase allowed energy difference
                samples           = 384000,
                substeps          = 3,
                timestep          = 0.5,
                blocks            = 10,
                warmupsteps       = 1000,
                dependencies      = orbdeps+[(optJ2_2,'jastrow')],
            )
            

            # run VMC with J3 results
            qmc_vmc_J3_1 = generate_qmcpack(
                identifier   = 'vmc_J3_1',
                path         = Mysystem+'/'+dftfunc+'/vmc_J3_1',
                job          = vmc_job,
                system       = system,
                jastrows     = [],
                pseudos      = 'ccecp',
                qmc          = 'vmc',
                warmupsteps  = 1000,
                blocks       = 100,
                steps        = max(int(48000/calc_cores),1),
                substeps     = 3,
                timestep     = 0.5,
                dependencies = orbdeps+[(optJ3_1,'jastrow')],
            )

            
            # Independent DMC runs at various timesteps
            qmc = generate_qmcpack(
                identifier    = 'dmc_J123_dt005',
                path          = Mysystem+'/'+dftfunc+'/dmc_J123_dt005',
                job           = dmc_job,
                system        = system,
                pseudos       = 'ccecp',
                jastrows      = [],
                qmc           = 'dmc',
                eq_dmc        = True,
                blocks        = 1600,
                steps         = 10,
                total_walkers = 9600,
                timestep      = 0.005,
                nonlocalmoves = "v3",
                dependencies  = orbdeps+[(optJ3_1,'jastrow')],
                )

            qmc = generate_qmcpack(
                identifier    = 'dmc_J123_dt015',
                path          = Mysystem+'/'+dftfunc+'/dmc_J123_dt015',
                job           = dmc_job,
                system        = system,
                pseudos       = 'ccecp',
                jastrows      = [],
                qmc           = 'dmc',
                eq_dmc        = True,
                blocks        = 1600,
                steps         = 10,
                total_walkers = 9600,
                timestep      = 0.015,
                nonlocalmoves = "v3",
                dependencies  = orbdeps+[(optJ3_1,'jastrow')],
                )
            
            qmc = generate_qmcpack(
                identifier    = 'dmc_J123_dt05',
                path          = Mysystem+'/'+dftfunc+'/dmc_J123_dt05',
                job           = dmc_job,
                system        = system,
                pseudos       = 'ccecp',
                jastrows      = [],
                qmc           = 'dmc',
                eq_dmc        = True,
                blocks        = 1600,
                steps         = 10,
                total_walkers = 9600,
                timestep      = 0.05,
                nonlocalmoves = "v3",
                dependencies  = orbdeps+[(optJ3_1,'jastrow')],
                )

run_project()

