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
        # collect dependencies relating to orbitals
        orbdeps = [(c4q,'particles'), # pyscf changes particle positions
                 (c4q,'orbitals' ),
                 (cc,'cuspcorr' )]

#### DMC BLOCKS FOR error bar analysis - through simulation length (Block)  
        # run DMC with cusp Correction and 1,2 and 3 Body Jastrow function 
        init_blocks=100
        for i in range(1,5):
            myblocks=init_blocks*i*i
            qmc = generate_qmcpack(
             identifier      = 'dmc_error'+str(i),
             seed            = 42,
             path            = 'Be2/'+y+'/'+x+'/dmc_error-bar',   # directory to run in
             job             = qmc_job,                  # Submit with the number of cores available
             system          = system,                                                                                  
             jastrows        = [],                                                                                      
             qmc             = 'dmc',                             # dmc run
             total_walkers   = 1024,                              # Number of Samples (selected from a VMC step)
             warmupsteps     = 50,                                # Number of Equilibration steps
             vmc_blocks      = 100,                               # Number of VMC blocks (To generate the DMC samples) 
             vmc_steps       = 10,                                # Number of VMC steps (To generate DMC samples)
             vmc_timestep    = 0.1,                               # VMC Timestep (To Generate DMC samples)
             timestep        = 0.00250,                           # DMC timestep
             blocks          = myblocks,                          # Number of DMC blocks
             dependencies    = orbdeps+[(optJ3,'jastrow')],       # Dependece (1B, 2B and 3B Jastrows)
             )
  
#### DMC BLOCKS FOR error bar analysis - through simulation length (Block)  
        # run DMC with cusp Correction and 1,2 and 3 Body Jastrow function 
        qmc = generate_qmcpack(
          identifier      = 'dmc_pop',
          seed            = 42,
          path            = 'Be2/'+y+'/'+x+'/dmc_error-bar',   # directory to run in
          job             = qmc_job,                  # Submit with the number of cores available
          system          = system,                                                                                  
          jastrows        = [],                                                                                      
          qmc             = 'dmc',                             # dmc run
         total_walkers     = 4026,                              # Number of Samples (selected from a VMC step)
          warmupsteps     = 50,                                # Number of Equilibration steps
          vmc_blocks      = 100,                               # Number of VMC blocks (To generate the DMC samples) 
          vmc_steps       = 10,                                # Number of VMC steps (To generate DMC samples)
          vmc_timestep    = 0.1,                               # VMC Timestep (To Generate DMC samples)
          timestep        = 0.00250,                           # DMC timestep
          blocks          = 100,                               # Number of DMC blocks
          dependencies    = orbdeps+[(optJ3,'jastrow')],       # Dependece (1B, 2B and 3B Jastrows)
          )
  
   
run_project()

