from nexus import settings,job
from nexus import generate_physical_system


settings(
    results    = '',
    sleep      = 3,
    machine    = 'ws4',
    status_only  = 0,
    pseudo_dir  = './pseudos/'
    )


system = generate_physical_system(
    units        = 'A',
    elem        = ['O','O'],
    pos         = [[0.000000, 0.000000, 0.000000],
                  [0.000000, 0.00000, 1.208]],
    O=6,
    )

cores = 4
qmc_job = job(cores=cores,threads=cores)
