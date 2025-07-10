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

        qmc = generate_qmcpack(
          identifier      = 'dmc',
          seed            = 42,
          path            = 'Be2/'+y+'/'+x+'/dmc_tstep',       # directory to run in
          job               = qmc_job,
          system          = system,                                                                                  
          jastrows        = [],                                                                                      
          qmc             = 'dmc',                             # dmc run
          warmupsteps     = 50,                                # Number of Equilibration steps
          vmc_blocks      = 200,                               # Number of VMC blocks (To generate the DMC samples) 
          vmc_steps       = 20,                                # Number of VMC steps (To generate DMC samples)
          vmc_timestep    = 0.3,                               # VMC Timestep (To Generate DMC samples)
          timestep        = 0.01,                              # DMC timestep
          timestep_factor = 0.5,                               # Reduce by 1/2
          ntimesteps      = 4,                                 # 4 times, i.e. [0.01, 0.005, 0.0025, 0.00125] timesteps
          total_walkers   = 1024,                              # Total walkers (selected from a VMC step)
          blocks          = 400,                               # Number of DMC blocks
          dependencies    = orbdeps+[(optJ3,'jastrow')],       # Dependence (1B and 2B Jastrows)
          )
   
run_project()
   
