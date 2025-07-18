#! /usr/bin/env python3

from nexus import settings,job,run_project,obj
from nexus import ppset
from nexus import generate_physical_system
from nexus import generate_pyscf
from nexus import generate_convert4qmc
from nexus import generate_cusp_correction
from nexus import generate_qmcpack
from be2_setup import system,qmc_job
# Obtain the core count of the local machine (lab only)

XC=["PBE"]                                             #Loop around multiple XC functionals
MyBasis=["cc-pvtz"]                                     #Loop around multiple basis sets  
for x in XC:
    for y in MyBasis:
        # perform DFT 
        scf = generate_pyscf(
            identifier = 'scf',                         # log output goes to scf.out
            path       = 'Be2/'+y+'/'+x+'/scf',         # directory to run in
            job        = job(serial=True,app='python3'),# pyscf must run serially         
            system     = system,
            mole       = obj(                           # used to make Mole() inputs
                basis    = y, 
                symmetry = True,
                verbose  = 5,
                ),
            calculation = obj(
                method      = 'ROKS',                   # Restricted Orbital Kohn Sham
                df_fitting  = True,                     # Density fitting
                max_cycle   = 200,                      # Max scf cycles
                level_shift = 0.0,                      # Mixing orbitals for convergence
                tol         = '1e-10',                  # Accuracy needed for convergence
                xc          = x,                        # Exchange and correlation functional                                     
                ),                                     
            save_qmc   = True ,                         # Save the orbital to QMCPACK format
            )




        # convert orbitals to QMCPACK format
        c4q = generate_convert4qmc(
          identifier   = 'c4q',
          path         = 'Be2/'+y+'/'+x+'/scf',         # directory to run in
          job          = job(cores=1),
          dependencies = (scf,'orbitals'),              # Create a dependency to DFT success
          )
   
        # calculate cusp correction
        cc = generate_cusp_correction(
          identifier   = 'cusp',                        
          path         = 'Be2/'+y+'/'+x+'/cuspcorr',         # directory to run in
          job          = qmc_job,
          system       = system,
          dependencies = (c4q,'orbitals'),              #Create dependency to converter
          )
   
        # collect dependencies relating to orbitals
        orbdeps = [(c4q,'particles'),                   # pyscf changes particle positions
                 (c4q,'orbitals' ),
                 (cc,'cuspcorr' )]

        # run VMC with cusp Correction and no Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'vmc',
          path         = 'Be2/'+y+'/'+x+'/vmc_cusp_noJ',# directory to run in
          job          = qmc_job,
          system       = system,
          driver       = 'batched',
          jastrows     = [],
          qmc          = 'vmc',                         # vmc run
          seed         = 42,
          warmupsteps  = 10,                            # equilibration steps
          blocks       = 100,                           # number of blocks
          steps        =   10,                          # number of steps to avoid autocorellation
          timestep     = 0.1,                           # timestep
          dependencies = orbdeps,
          )
run_project()
