#! /usr/bin/env python3

from nexus import settings,job,run_project,obj
from nexus import ppset
from nexus import generate_physical_system
from nexus import generate_pyscf
from nexus import generate_convert4qmc
from nexus import generate_cusp_correction
from nexus import generate_qmcpack
from be2_setup import system, qmc_job

XC=["PBE"]
MyBasis=["cc-pvtz"]
for x in XC:
    for y in MyBasis:
        # perform DFT 
        scf = generate_pyscf(
            identifier = 'scf',               # log output goes to scf.out
            path       = 'Be2/'+y+'/'+x+'/scf',         # directory to run in
            job        = job(serial=True,app='python3'),    # pyscf must run serially         
            system     = system,
            mole       = obj(                 # used to make Mole() inputs
                basis    = y, 
                symmetry = True,
                verbose       = 5,
                ),
            calculation = obj(
                method      = 'ROKS',
                df_fitting  = True,
                xc          = x,
                max_cycle  = 200,
                level_shift  = 0.0,
                tol        = '1e-10',
                ),
            save_qmc   = True ,
            )


        # convert orbitals to QMCPACK format
        c4q = generate_convert4qmc(
          identifier   = 'c4q',
          path       = 'Be2/'+y+'/'+x+'/scf',         # directory to run in
          job          = job(cores=1),
          add_cusp      = True, 
          dependencies = (scf,'orbitals'),
          )
   
        # calculate cusp correction
        cc = generate_cusp_correction(
          identifier   = 'cusp',
          path         = 'Be2/'+y+'/'+x+'/cuspcorr',         # directory to run in
          job          = job(cores=4),
          system       = system,
          dependencies = (c4q,'orbitals'),
          )
   
        # collect dependencies relating to orbitals
        orbdeps = [(c4q,'particles'), # pyscf changes particle positions
                 (c4q,'orbitals' ),
                 (cc,'cuspcorr' )]


        # optimize 2-body Jastrow
        optJ2 = generate_qmcpack(
          identifier        = 'opt',
          path              = 'Be2/'+y+'/'+x+'/optJ2',         # directory to run in
          job               = qmc_job,
          system            = system,
          J2                = True,         # 2-body B-spline Jastrow
          J1_rcut           = 6.0,          # 6 Bohr cutoff for J1
          J2_rcut           = 8.0,          # 8 Bohr cutoff for J2
          seed              = 42,           # Fix the seed (lab only)
          qmc               = 'opt',        # Wavefunction optimization run
          minmethod         = 'oneshift',   # Energy minimization
          warmupsteps       = 10,
          blocks            = 20,
          timestep          = 0.1,
          minwalkers        = 0.5,
          samples           = 25600,        # VMC samples per iteration
          dependencies      = orbdeps,
          )
   

        # optimize 3-body Jastrow
        optJ3 = generate_qmcpack(
          identifier        = 'opt',
          path              = 'Be2/'+y+'/'+x+'/optJ3',         # directory to run in
          job               = qmc_job,
          system            = system,
          J3                = True,         # 3-body B-spline Jastrow
          seed              = 42,           # Fix the seed (lab only)
          qmc               = 'opt',        # Wavefunction optimization run
          minmethod         = 'oneshift',   # Energy minimization
          init_cycles       = 4,            # 4 iterations allowing larger parameter changes
          cycles            = 8,            # 8 production iterations
          warmupsteps       = 10,
          blocks            = 20,
          timestep          = 0.1,
          init_minwalkers   = 0.1,
          minwalkers        = 0.5,
          samples           = 25600,        # VMC samples per iteration
          dependencies      = orbdeps+[(optJ2,'jastrow')],
          )


#### VMC BLOCKS TO ASSES EFFECTS OF JASTROWS

        # run VMC with cusp Correction and no Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'vmc',
          path         = 'Be2/'+y+'/'+x+'/vmc_NoJ',         # directory to run in
          job               = qmc_job,
          driver       = 'batched',
          system       = system,
          jastrows     = [],
          qmc          = 'vmc',                             # vmc run
          seed         = 42,                                # Fix the seed (lab only)          
          warmupsteps  = 30,                                # Number of Equilibration steps
          blocks       = 400,                               # Number of blocks 
          timestep     = 0.1,                               # Time Step
          dependencies = orbdeps,                           # Dependece (No Jastrows)
          )

        # run VMC with cusp Correction and 1,2 Body Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'vmc',
          path         = 'Be2/'+y+'/'+x+'/vmc_2J',          # directory to run in 
          driver       = 'batched',
          job               = qmc_job,
          system       = system,                                                                        
          jastrows     = [],                                                                            
          qmc          = 'vmc',                             # vmc run
          seed         = 42,                                # Fix the seed (lab only)          
          warmupsteps  = 30,                                # Number of Equilibration steps
          blocks       = 400,                               # Number of blocks 
          timestep     = 0.1,                               # Time Step
          dependencies = orbdeps+[(optJ2,'jastrow')],       # Dependece (1B and 2B Jastrows)
          )
   
   
        # run VMC with cusp Correction and 1,2 Body Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'vmc',
          path         = 'Be2/'+y+'/'+x+'/vmc_3J',          # directory to run in                        
          job               = qmc_job,
          driver       = 'batched',
          system       = system,                                                                        
          jastrows     = [],                                                                            
          qmc          = 'vmc',                             # vmc run
          seed         = 42,                                # Fix the seed (lab only)          
          warmupsteps  = 30,                                # Number of Equilibration steps
          blocks       = 400,                               # Number of blocks 
          timestep     = 0.1,                               # Time Step
          dependencies = orbdeps+[(optJ3,'jastrow')],       # Dependece (1B, 2B and 3B Jastrows)
          )


#### DMC BLOCKS TO ASSES EFFECTS OF JASTROWS

        # run DMC with cusp Correction and no Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'dmc',
          seed         = 42,
          path         = 'Be2/'+y+'/'+x+'/dmc_NoJ',         # directory to run in
          job               = qmc_job,
          driver       = 'batched',
          system       = system,
          jastrows     = [],
          qmc          = 'dmc',                             # dmc run
          total_walkers = 1024,                              # Number of Samples (selected from a VMC step)
          warmupsteps  = 50,                                # Number of Equilibration steps
          vmc_blocks   = 50,                                # Number of VMC blocks (To generate the DMC samples) 
          vmc_steps    = 20,                                # Number of VMC steps (To generate DMC samples)
          vmc_timestep = 0.1,                               # VMC Timestep (To Generate DMC samples)
          timestep     = 0.01,                              # DMC timestep
          blocks       =  250,                              # Number of DMC blocks
          dependencies = orbdeps,                           # Dependece (No Jastrows)
          )


        # run DMC with cusp Correction and 1,2 Body Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'dmc',
          seed         = 42,
          path         = 'Be2/'+y+'/'+x+'/dmc_2J',          # directory to run in
          job               = qmc_job,
          driver       = 'batched',
          system       = system,                                                                                  
          jastrows     = [],                                                                                      
          qmc          = 'dmc',                             # dmc run
          total_walkers = 1024,                              # Number of Samples (selected from a VMC step)
          warmupsteps  = 50,                                # Number of Equilibration steps
          vmc_blocks   = 50,                                # Number of VMC blocks (To generate the DMC samples) 
          vmc_steps    = 20,                                # Number of VMC steps (To generate DMC samples)
          vmc_timestep = 0.1,                               # VMC Timestep (To Generate DMC samples)
          timestep     = 0.01,                              # DMC timestep
          blocks       =  250,                              # Number of DMC blocks
          dependencies = orbdeps+[(optJ2,'jastrow')],       # Dependece (1B and 2B Jastrows)
          )
 
   
        # run DMC with cusp Correction and 1,2 and 3 Body Jastrow function 
        qmc = generate_qmcpack(
          identifier   = 'dmc',
          seed         = 42,
          path         = 'Be2/'+y+'/'+x+'/dmc_3J',          # directory to run in
          job               = qmc_job,
          driver       = 'batched',
          system       = system,                                                                                  
          jastrows     = [],                                                                                      
          qmc          = 'dmc',                             # dmc run
          total_walkers = 1024,                              # Number of Samples (selected from a VMC step)
          warmupsteps  = 50,                                # Number of Equilibration steps
          vmc_blocks   = 50,                                # Number of VMC blocks (To generate the DMC samples) 
          vmc_steps    = 20,                                # Number of VMC steps (To generate DMC samples)
          vmc_timestep = 0.1,                               # VMC Timestep (To Generate DMC samples)
          timestep     = 0.01,                              # DMC timestep
          blocks       =  250,                              # Number of DMC blocks
          dependencies = orbdeps+[(optJ3,'jastrow')],       # Dependece (1B and 2B Jastrows)
          )
   
run_project()
   
