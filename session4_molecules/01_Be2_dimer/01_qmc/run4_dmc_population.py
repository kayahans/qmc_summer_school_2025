#! /usr/bin/env python3

from nexus import settings,job,run_project,obj
from nexus import ppset
from nexus import generate_physical_system
from nexus import generate_pyscf
from nexus import generate_convert4qmc
from nexus import generate_cusp_correction
from nexus import generate_qmcpack
from be2_setup import system,qmc_job
from run1_wfopt import c4q, cc, optJ3

XC=["PBE"]
MyBasis=["cc-pvtz"]
for x in XC:
    for y in MyBasis:
        # perform DFT 
        orbdeps = [(c4q,'particles'), # pyscf changes particle positions
                 (c4q,'orbitals' ),
                 (cc,'cuspcorr' )]
        pop=64
        while pop<2049:
           qmc = generate_qmcpack(
             identifier      = 'dmc_pop'+str(pop),
             seed            = 42,
             path            = 'Be2/'+y+'/'+x+'/dmc_pop',         # directory to run in
             job             = qmc_job,                  # Submit with the number of cores available
             system          = system,                                                                                  
             jastrows        = [],                                                                                      
             qmc             = 'dmc',                             # dmc run
             total_walkers   = pop,                               # Number of Samples (selected from a VMC step)
             warmupsteps     = 0,                                 # Number of Equilibration steps
             vmc_blocks      = 10,                                # Number of VMC blocks (To generate the DMC samples) 
             vmc_steps       = 1,                                 # Number of VMC steps (To generate DMC samples)
             vmc_timestep    = 0.3,                               # VMC Timestep (To Generate DMC samples)
             timestep        = 0.01,                              # DMC timestep
             steps           = 20480//pop,                        # number of step*population maintained constant to maintain error bar  
             blocks          = 10,                                # Number of DMC blocks
             dependencies    = orbdeps+[(optJ3,'jastrow')],       # Dependece (1B and 2B Jastrows)
             )
           pop=pop*2  
run_project()
