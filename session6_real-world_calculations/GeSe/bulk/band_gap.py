#!/usr/bin/env python3

import os
cores = os.cpu_count()

from nexus import settings,job,run_project
from nexus import generate_physical_system,read_structure
from nexus import generate_pwscf
from nexus import generate_pw2qmcpack
from nexus import generate_qmcpack,vmc,dmc
from nexus import ppset,obj
from nexus import get_machine
from qmcpack_input import spindensity


settings(
    pseudo_dir    = '../pseudopotentials',
    results       = '',
    sleep         = 3,
    machine       = 'ws'+str(cores),
    status_only   = 0,
    generate_only = 0,
    progress_tty  = 1,
    )





dft_shared = obj(
    input_type       = 'generic',
    input_dft        = 'pbe',
    ecutwfc          = 100, # LAB-ONLY!! Nedd to check convergence for the science production. 
    occupations      = 'smearing',
    smearing         = 'fermi-dirac',
    degauss          = 1e-3,
    mixing_beta      = 0.5,
    nspin            = 2,
    start_mag        = obj(Ge=0.2),
    kshift           = (0,0,0),
    pseudos          = ['Ge.ccECP.upf','Se.ccECP.upf'],
    )

qmc_shared = obj(
    driver         = 'batched',
    input_type     = 'basic',
    meshfactor     = 1.00,
    spin_polarized = True,
    pseudos        = ['Ge.ccECP.xml','Se.ccECP.xml'],
    )

system = generate_physical_system(
    units  = 'A',                      # Angstrom units
    axes   = [[4.38,0.,0.   ],     # cell axes
              [0.   ,3.82,0.],
              [0.,0.   ,10.79]],    
    elem   = ['Ge','Ge','Ge','Ge','Se','Se','Se','Se'],                # 4 Ge and 4 Se atoms
    posu    = [[0.106    ,0.25    ,0.879    ],  # atomic positions
              [0.394    ,0.25    ,0.379    ],
              [0.894    ,0.75    ,0.121    ],
              [0.606    ,0.75    ,0.621    ],
              [0.503    ,0.25    ,0.148    ],
              [0.997    ,0.25    ,0.648    ],
              [0.497    ,0.75    ,0.852    ],
              [0.003    ,0.75    ,0.352    ]],
    net_spin   = 0,
    net_charge = 0,
    tiling     = [[1, 0, 0],[0, 1, 0],[0, 0, 1]],                 # tile to 8 atom cell
#    symm_kgrid = True,
    kgrid  = (1,1,1),                  # 1x1x1 twists
    kshift = (0,0,0),                  #  at gamma
    Ge      = 4,                         # pseudo-Ge (4 val. elec.)    
    Se      = 6,                         # pseudo-Se (6 val. elec.)
 )

basepath = './'

scf = generate_pwscf(
    identifier        = 'scf',
    path              = basepath + 'scf',
    job               = job(cores=cores, app='pw.x'),
    calculation       = 'scf',
    system            = system,
    kgrid             = (2,2,1),  # LAB-ONLY!! Nedd to check convergence for the science production.
    **dft_shared
    )

nscf = generate_pwscf(
    identifier        = 'nscf',
    path              = basepath + 'nscf',
    job               = job(cores=cores, app='pw.x'),
    calculation       = 'nscf',
    system            = system,
    nosym             = True,
    nogamma           = True,
    dependencies      = (scf,'charge_density'),
    **dft_shared
    )

p2q = generate_pw2qmcpack(
    identifier        = 'p2q',
    path              = basepath + 'nscf',
    job               = job(cores=cores,app='pw2qmcpack.x'),
    write_psir        = False,
    dependencies      = (nscf,'orbitals'),
    )

optJ12 = generate_qmcpack(
    identifier           = 'optJ12',
    path                 = basepath + 'optJ12',
    job                  = job(cores=cores,app='qmcpack'),
    system               = system,
    twistnum             = 0,
    qmc                  = 'opt',
    J2                   = True,
    minmethod            = 'oneshift',
    warmupsteps          = 10,
    init_cycles          = 5,
    cycles               = 5,
    samples              = 12800,
    blocks               = 10,
    substeps                = 20,
    minwalkers           = 0.3,
    corrections          = [],
    dependencies         = (p2q,'orbitals'),
    **qmc_shared
    )

J3_rcut = system.structure.rwigner()

optJ123 = generate_qmcpack(
    identifier           = 'optJ123',
    path                 = basepath + 'optJ123',
    job                  = job(cores=cores,app='qmcpack'),
    system               = system,
    twistnum             = 0,
    qmc                  = 'opt',
    J2                   = True,
    J3                   = True,
    J3_rcut              = J3_rcut,
    minmethod            = 'oneshift',
    warmupsteps          = 10,
    init_cycles          = 0,
    cycles               = 10,
    samples              = 12800,
    blocks               = 10,
    substeps                = 20,
    minwalkers           = 0.5,
    corrections          = [],
    dependencies         = [(p2q,'orbitals'), (optJ12,'jastrow')],
    **qmc_shared
    )

qmc = generate_qmcpack(
#   skip_submit          = True,
    identifier           = 'qmc',
    path                 = basepath + 'qmc',
    job                  = job(cores=cores,app='qmcpack'),
    system               = system,
    calculations         = [
    vmc(
        total_walkers = 256,
        warmupsteps      = 100,
        blocks           = 20,
        steps            = 50,
        timestep         = 0.3,
        ),
    dmc( # main dmc
        total_walkers = 256,
        timestep         = 0.01,
        warmupsteps      = 100,
        blocks           = 100,
        steps            = 20,
        nonlocalmoves    = 'v3',
        ),
    ],
    dependencies         = [(p2q,'orbitals'), (optJ123,'jastrow')],
    **qmc_shared
    )

qmc_excitonic_gap = generate_qmcpack(
#   skip_submit          = True,
    identifier           = 'qmc',
    path                 = basepath + 'qmc_excitonic_gap',
    job                  = job(cores=cores,app='qmcpack'),
    system               = system,
    det_format = "old",
    excitation           = ['up', '0 19 0 20'],
#    excitation = ['up', '-20 + 21'],
    calculations         = [
    vmc(
        total_walkers = 256,
        warmupsteps      = 100,
        blocks           = 20,
        steps            = 20,
        timestep         = 0.3,
        ),
    dmc( # main dmc
        total_walkers     = 256,
        timestep         = 0.01,
        warmupsteps      = 100,
        blocks           = 100,
        steps            = 20,
        nonlocalmoves    = 'v3',
        ),
    ],
    dependencies         = [(p2q,'orbitals'), (optJ123,'jastrow')],
    **qmc_shared
    )

qmc_QP_minus = generate_qmcpack(
#   skip_submit          = True,
    identifier           = 'qmc',
    path                 = basepath + 'qmc_QP_minus',
    job                  = job(cores=cores,app='qmcpack'),
    system               = system,
    det_format = "old",    
    calculations         = [
    vmc(
        total_walkers    = 256,
        warmupsteps      = 100,
        blocks           = 20,
        steps            = 20,
        timestep         = 0.3,
        ),
    dmc( # main dmc
        total_walkers    = 256,
        timestep         = 0.01,
        warmupsteps      = 100,
        blocks           = 100,
        steps            = 20,
        nonlocalmoves    = 'v3',
        ),
    ],
    dependencies         = [(p2q,'orbitals'), (optJ123,'jastrow')],
    **qmc_shared
    )

u = qmc_QP_minus.input.get('u')
u.size-=1
updet = qmc_QP_minus.input.get('updet')
updet.size-=1

qmc_QP_plus = generate_qmcpack(
#   skip_submit          = True,
    identifier           = 'qmc',
    path                 = basepath + 'qmc_QP_plus',
    job                  = job(cores=cores,app='qmcpack'),
    system               = system,
    det_format = "old",    
    calculations         = [
    vmc(
        total_walkers = 256,
        warmupsteps      = 100,
        blocks           = 20,
        steps            = 20,
        timestep         = 0.3,
        ),
    dmc( # main dmc
        total_walkers = 256,
        timestep         = 0.01,
        warmupsteps      = 1000,
        blocks           = 100,
        steps            = 20,
        nonlocalmoves    = 'v3',
        ),
    ],
    dependencies         = [(p2q,'orbitals'), (optJ123,'jastrow')],
    **qmc_shared
    )


u = qmc_QP_plus.input.get('u')
u.size+=1
updet = qmc_QP_plus.input.get('updet')
updet.size+=1
 
run_project()

