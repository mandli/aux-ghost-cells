# encoding: utf-8
"""
Module to set up run time parameters for Clawpack.

The values set in the function setrun are then written out to data files
that will be read in by the Fortran code.

"""

from pathlib import Path
import os
import datetime
import shutil
import gzip
import numpy as np

import clawpack.clawutil.data as data
from clawpack.geoclaw.surge.storm import Storm
import clawpack.clawutil as clawutil


#                           days   s/hour    hours/day            
days2seconds = lambda days: days * 60.0**2 * 24.0
seconds2days = lambda seconds: seconds / (60.0**2 * 24.0)

RAMP_UP_TIME = 0.5  # In days
# In this case we simply use the default base_date in the surge.data module
tracy_landfall = datetime.datetime(2008, 8, 1, 12) - datetime.datetime(2008,1,1,0)

# Scratch directory for storing topo and storm files:
CLAW = Path(os.environ["CLAW"])
scratch_dir = CLAW / 'geoclaw' / 'scratch'

#------------------------------
def setrun(claw_pkg='geoclaw'):
#------------------------------

    """
    Define the parameters used for running Clawpack.

    INPUT:
        claw_pkg expected to be "geoclaw" for this setrun.

    OUTPUT:
        rundata - object of class ClawRunData

    """

    assert claw_pkg.lower() == 'geoclaw',  "Expected claw_pkg = 'geoclaw'"

    ndim = 2
    rundata = data.ClawRunData(claw_pkg, ndim)

    #------------------------------------------------------------------
    # Problem-specific parameters to be written to setprob.data:
    #------------------------------------------------------------------

    #probdata = rundata.new_UserData(name='probdata',fname='setprob.data')

    #------------------------------------------------------------------
    # Standard Clawpack parameters to be written to claw.data:
    #   (or to amr2ez.data for AMR)
    #------------------------------------------------------------------

    clawdata = rundata.clawdata  # initialized when rundata instantiated


    # Set single grid parameters first.
    # See below for AMR parameters.


    # ---------------
    # Spatial domain:
    # ---------------

    # Number of space dimensions:
    clawdata.num_dim = ndim

    # Lower and upper edge of computational domain:
    clawdata.lower[0] = -115.0
    clawdata.upper[0] = -65.0
    
    clawdata.lower[1] = 0.0
    clawdata.upper[1] = 50.0

    # Number of grid cells:
    clawdata.num_cells[0] = 200
    clawdata.num_cells[1] = 200
    # ---------------
    # Size of system:
    # ---------------

    # Number of equations in the system:
    clawdata.num_eqn = 3

    # Number of auxiliary variables in the aux array (initialized in setaux)
    clawdata.num_aux = 4 + 3 + 2

    # Index of aux array corresponding to capacity function, if there is one:
    clawdata.capa_index = 2



    # -------------
    # Initial time:
    # -------------

    clawdata.t0 = 0 #-days2seconds(3)
    clawdata.tfinal = days2seconds(4)

    # Restart from checkpoint file of a previous run?
    # Note: If restarting, you must also change the Makefile to set:
    #    RESTART = True
    # If restarting, t0 above should be from original run, and the
    # restart_file 'fort.chkNNNNN' specified below should be in 
    # the OUTDIR indicated in Makefile.

    clawdata.restart = False               # True to restart from prior results
    clawdata.restart_file = 'fort.chk00006'  # File to use for restart data


    # -------------
    # Output times:
    #--------------

    # Specify at what times the results should be written to fort.q files.
    # Note that the time integration stops after the final output time.
    # The solution at initial time t0 is always written in addition.

    clawdata.output_style = 3 # previously 2

    if clawdata.output_style==1:
        # Output nout frames at equally spaced times up to tfinal:
        # clawdata.tfinal = days2seconds(date2days('2008091400'))
        
        recurrence = 4 # previously 24
        clawdata.num_output_times = int((clawdata.tfinal - clawdata.t0) 
                                            * recurrence / (60**2 * 24))

        clawdata.output_t0 = True  # output at initial (or restart) time?

    elif clawdata.output_style == 2:
        # Specify a list of output times.
        clawdata.output_t0 = True  # output at initial (or restart) time?
        clawdata.output_times = [days2seconds(tracy_landfall.days) + tracy_landfall.seconds + delta_t for delta_t in range(-1*60**2, 100, 500)]

    elif clawdata.output_style == 3:
        # Output every iout timesteps with a total of ntot time steps:
        clawdata.output_step_interval = 1
        clawdata.total_steps = 10
        clawdata.output_t0 = True


    clawdata.output_format = 'ascii'      # 'ascii' or 'netcdf' 

    clawdata.output_q_components = 'all'   # could be list such as [True,True]
    clawdata.output_aux_components = 'all' # could be list
    clawdata.output_aux_onlyonce = False    # output aux arrays only at t0


    # ---------------------------------------------------
    # Verbosity of messages to screen during integration:
    # ---------------------------------------------------

    # The current t, dt, and cfl will be printed every time step
    # at AMR levels <= verbosity.  Set verbosity = 0 for no printing.
    #   (E.g. verbosity == 2 means print only on levels 1 and 2.)
    clawdata.verbosity = 0 # previously 1




    # --------------
    # Time stepping:
    # --------------

    # if dt_variable==1: variable time steps used based on cfl_desired,
    # if dt_variable==0: fixed time steps dt = dt_initial will always be used.
    clawdata.dt_variable = True

    # Initial time step for variable dt.
    # If dt_variable==0 then dt=dt_initial for all steps:
    clawdata.dt_initial = 0.016

    # Max time step to be allowed if variable dt used:
    clawdata.dt_max = 1e+99

    # Desired Courant number if variable dt used, and max to allow without
    # retaking step with a smaller dt:
    clawdata.cfl_desired = 0.75
    clawdata.cfl_max = 1.0
    # clawdata.cfl_desired = 0.25
    # clawdata.cfl_max = 0.5

    # Maximum number of time steps to allow between output times:
    clawdata.steps_max = 2**16




    # ------------------
    # Method to be used:
    # ------------------

    # Order of accuracy:  1 => Godunov,  2 => Lax-Wendroff plus limiters
    clawdata.order = 2
    
    # Use dimensional splitting? (not yet available for AMR)
    clawdata.dimensional_split = 'unsplit'
    
    # For unsplit method, transverse_waves can be 
    #  0 or 'none'      ==> donor cell (only normal solver used)
    #  1 or 'increment' ==> corner transport of waves
    #  2 or 'all'       ==> corner transport of 2nd order corrections too
    clawdata.transverse_waves = 2

    # Number of waves in the Riemann solution:
    clawdata.num_waves = 3
    
    # List of limiters to use for each wave family:  
    # Required:  len(limiter) == num_waves
    # Some options:
    #   0 or 'none'     ==> no limiter (Lax-Wendroff)
    #   1 or 'minmod'   ==> minmod
    #   2 or 'superbee' ==> superbee
    #   3 or 'mc'       ==> MC limiter
    #   4 or 'vanleer'  ==> van Leer
    clawdata.limiter = ['mc', 'mc', 'mc']

    clawdata.use_fwaves = True    # True ==> use f-wave version of algorithms
    
    # Source terms splitting:
    #   src_split == 0 or 'none'    ==> no source term (src routine never called)
    #   src_split == 1 or 'godunov' ==> Godunov (1st order) splitting used, 
    #   src_split == 2 or 'strang'  ==> Strang (2nd order) splitting used,  not recommended.
    clawdata.source_split = 'godunov'
    # clawdata.source_split = 'strang'


    # --------------------
    # Boundary conditions:
    # --------------------

    # Number of ghost cells (usually 2)
    clawdata.num_ghost = 2

    # Choice of BCs at xlower and xupper:
    #   0 => user specified (must modify bcN.f to use this option)
    #   1 => extrapolation (non-reflecting outflow)
    #   2 => periodic (must specify this at both boundaries)
    #   3 => solid wall for systems where q(2) is normal velocity

    clawdata.bc_lower[0] = 'extrap'
    clawdata.bc_upper[0] = 'extrap'

    clawdata.bc_lower[1] = 'extrap'
    clawdata.bc_upper[1] = 'extrap'

    # Specify when checkpoint files should be created that can be
    # used to restart a computation.

    clawdata.checkpt_style = 0

    if clawdata.checkpt_style == 0:
        # Do not checkpoint at all
        pass

    elif clawdata.checkpt_style == 1:
        # Checkpoint only at tfinal.
        pass

    elif clawdata.checkpt_style == 2:
        # Specify a list of checkpoint times.  
        clawdata.checkpt_times = [0.1,0.15]

    elif clawdata.checkpt_style == 3:
        # Checkpoint every checkpt_interval timesteps (on Level 1)
        # and at the final time.
        clawdata.checkpt_interval = 5


    # ---------------
    # AMR parameters:
    # ---------------
    amrdata = rundata.amrdata

    amrdata.max1d = 400

    # max number of refinement levels:
    amrdata.amr_levels_max = 2

    # List of refinement ratios at each level (length at least mxnest-1)
    # Run resolution.py 2 2 4 8 16 to see approximate resolutions
    amrdata.refinement_ratios_x = [2,2,2,2,2]
    amrdata.refinement_ratios_y = [2,2,2,2,2]
    amrdata.refinement_ratios_t = [2,2,2,2,2]


    # Specify type of each aux variable in amrdata.auxtype.
    # This must be a list of length maux, each element of which is one of:
    #   'center',  'capacity', 'xleft', or 'yleft'  (see documentation).

    amrdata.aux_type = ['center','capacity','center','center','center',
                         'center','center','center','center']


    # Flag using refinement routine flag2refine rather than richardson error
    amrdata.flag_richardson = False    # use Richardson?
    amrdata.flag2refine = True

    # steps to take on each level L between regriddings of level L+1:
    amrdata.regrid_interval = 3

    # width of buffer zone around flagged points:
    # (typically the same as regrid_interval so waves don't escape):
    amrdata.regrid_buffer_width  = 2

    # clustering alg. cutoff for (# flagged pts) / (total # of cells refined)
    # (closer to 1.0 => more small grids may be needed to cover flagged cells)
    amrdata.clustering_cutoff = 0.700000

    # print info about each regridding up to this level:
    amrdata.verbosity_regrid = 2

    #  ----- For developers ----- 
    # Toggle debugging print statements:
    amrdata.dprint = False      # print domain flags
    amrdata.eprint = False      # print err est flags
    amrdata.edebug = False      # even more err est flags
    amrdata.gprint = False      # grid bisection/clustering
    amrdata.nprint = False      # proper nesting output
    amrdata.pprint = False      # proj. of tagged points
    amrdata.rprint = True       # print regridding summary
    amrdata.sprint = False      # space/memory output
    amrdata.tprint = False      # time step reporting each level
    amrdata.uprint = False      # update/upbnd reporting
    
    # More AMR parameters can be set -- see the defaults in pyclaw/data.py

    rundata.regiondata.regions = []
    # to specify regions of refinement append lines of the form
    #  [minlevel,maxlevel,t1,t2,x1,x2,y1,y2]
    x = (clawdata.upper[0] - clawdata.lower[0]) / 2 + clawdata.lower[0]
    y = (clawdata.upper[1] - clawdata.lower[1]) / 2 + clawdata.lower[1]
    rundata.regiondata.regions.append([2, 2, clawdata.t0, clawdata.tfinal, 
                                             x - 1, x + 1, y - 1, y + 1])

    # == setgauges.data values ==
    rundata.gaugedata.aux_out_fields = [0, 4, 5, 6]
    gauges = rundata.gaugedata.gauges
    epsilon = 0.13
    x = (clawdata.upper[0] - clawdata.lower[0]) / 2 + clawdata.lower[0]
    y = (clawdata.upper[1] - clawdata.lower[1]) / 2 + clawdata.lower[1]
    gauges.append([0, x, y, clawdata.t0, clawdata.tfinal])
    gauge_id = 1
    gauges.append([gauge_id,     x + epsilon, y + epsilon, clawdata.t0, clawdata.tfinal])
    gauges.append([gauge_id + 1, x - epsilon, y + epsilon, clawdata.t0, clawdata.tfinal])
    gauges.append([gauge_id + 2, x - epsilon, y - epsilon, clawdata.t0, clawdata.tfinal])
    gauges.append([gauge_id + 3, x + epsilon, y - epsilon, clawdata.t0, clawdata.tfinal])
    gauge_sets = 5
    for n in range(1, gauge_sets + 1):
        gauge_id = (n - 1) * 8 + 5
        # print(f"{gauge_id} - {gauge_id + 8}")
        # UR
        gauges.append([gauge_id,     x + epsilon, y + epsilon * n, clawdata.t0, clawdata.tfinal])
        # UL
        gauges.append([gauge_id + 1, x - epsilon, y + epsilon * n, clawdata.t0, clawdata.tfinal])
        # LU
        gauges.append([gauge_id + 2, x - epsilon * n, y + epsilon, clawdata.t0, clawdata.tfinal])
        # RU
        gauges.append([gauge_id + 3, x + epsilon * n, y + epsilon, clawdata.t0, clawdata.tfinal])
        # DR
        gauges.append([gauge_id + 4, x + epsilon, y - epsilon * n, clawdata.t0, clawdata.tfinal])
        # DL
        gauges.append([gauge_id + 5, x - epsilon, y - epsilon * n, clawdata.t0, clawdata.tfinal])
        # LD
        gauges.append([gauge_id + 6, x - epsilon * n, y - epsilon, clawdata.t0, clawdata.tfinal])
        # RD
        gauges.append([gauge_id + 7, x + epsilon * n, y - epsilon, clawdata.t0, clawdata.tfinal])
        
    # for gauge in gauges:
    #     print(f"{gauge[0]}: ({gauge[1]}, {gauge[2]})")

    #------------------------------------------------------------------
    # GeoClaw specific parameters:
    #------------------------------------------------------------------

    rundata = setgeo(rundata)   # Defined below


    return rundata
    # end of function setrun
    # ----------------------


#-------------------
def setgeo(rundata):
#-------------------
    """
    Set GeoClaw specific runtime parameters.
    For documentation see ....
    """

    try:
        geo_data = rundata.geo_data
    except:
        print("*** Error, this rundata has no geodata attribute")
        raise AttributeError("Missing geodata attribute")
       
    # == Physics ==
    geo_data.gravity = 9.81
    geo_data.coordinate_system = 2
    geo_data.earth_radius = 6367.5e3
    # added
    geo_data.rho = 1025.0
    geo_data.rho_air = 1.15
    geo_data.ambient_pressure = 101.3e3

    # == Forcing Options
    geo_data.coriolis_forcing = True
    geo_data.friction_forcing = True
    geo_data.manning_coefficient = 0.025 # Overridden below
    geo_data.friction_depth = 1e6

    # == Algorithm and Initial Conditions ==
    geo_data.sea_level = 0.28  # Due to seasonal swelling of gulf
    geo_data.dry_tolerance = 1.e-2

    # Refinement Criteria
    refine_data = rundata.refinement_data
    refine_data.wave_tolerance = 5e-1
    refine_data.speed_tolerance = [0.25,0.5,1.0,2.0,3.0,4.0]
    refine_data.variable_dt_refinement_ratios = True

    # == settopo.data values ==
    topo_data = rundata.topo_data
    topo_data.test_topography = 2
    topo_data.topofiles = []

    # Based on approximately 100 km = 1 degree of long
    # geodata.x0 = rundata.clawdata.lower[0] + 3.5
    # geodata.x1 = rundata.clawdata.lower[0] + 4.5
    # geodata.x2 = rundata.clawdata.lower[0] + 4.8
    topo_data.x0 = rundata.clawdata.lower[0] + 3.5
    topo_data.x1 = rundata.clawdata.lower[0] + 4.5
    topo_data.x2 = rundata.clawdata.lower[0] + 4.8

    topo_data.basin_depth = -3000.0
    # geodata.basin_depth = -100.0
    # topo_data.shelf_depth = -200.0
    topo_data.shelf_depth = -3000.0
    # beach_height = 300.0
    # topo_data.beach_slope = -(beach_height + topo_data.shelf_depth) / (rundata.clawdata.upper[0] - topo_data.x2)
    topo_data.beach_slope = 0.05

    # == setqinit.data values ==
    rundata.qinit_data.qinit_type = 0
    
    # ================
    #  Set Surge Data
    # ================
    data = rundata.surge_data

   # Physics parameters
    # data.rho_air = 1.15             # Density of air (rho is not implemented above)
    # data.ambient_pressure = 101.5e3 # Nominal atmos pressure

    # Source term controls
    data.wind_forcing = True
    data.drag_law = 2
    data.pressure_forcing = True

    # AMR parameters, in m/s and meters respectively
    data.wind_refine = [20.0,40.0,60.0]
    data.R_refine = [60.0e3,40e3,20e3]
    
    # Storm parameters 
    data.storm_specification_type = "holland80" #previously 0
    data.storm_file = (Path() / 'my_storm.storm').resolve()

    # 16 time steps, because 6 hour steps in 4 days
    forecasts = 16
    my_storm = Storm(file_format="geoclaw")
    my_storm.time_offset = np.datetime64("2008-09-13T07")
    t_series = np.linspace(rundata.clawdata.t0, rundata.clawdata.tfinal, forecasts, dtype=int)
    my_storm.t = np.array([my_storm.time_offset + np.timedelta64(t, 's') 
                                for t in t_series])

    def storm_location(t):
        eye_init = (-80, 15)
        # 15 km / h -> 1 degree / 110 km * 1 h / 3600 s
        v = (-np.sqrt(2) * 15 / 110 / 3600, np.sqrt(2) * 15 / 110 / 3600)
        return [v[i] * t + eye_init[i] for i in range(2)]
    my_storm.eye_location = np.array(storm_location(t_series)).transpose()
    max_wind_speed = 100 * np.exp(-(t_series - (t_series[-1] / 2))**2 / (t_series[-1] / 4)**2)
    
    my_storm.max_wind_speed = max_wind_speed

    # Max Wind Radius
    C0 = 218.3784 * np.ones(max_wind_speed.shape[0])
    # print(storm.eye_location[:, 1].shape, storm.max_wind_speed.shape[0])
    my_storm.max_wind_radius = ( C0 - 1.2014 * max_wind_speed 
    + (max_wind_speed / 10.9884)**2 
    - (max_wind_speed / 35.3052)**3 
    - 145.5090 * np.cos(my_storm.eye_location[:, 1] * 0.0174533) )*1000

    # Add central pressure - From Kossin, J. P. WAF 2015
    a = -0.0025
    b = -0.36
    c = 1021.36
    my_storm.central_pressure = ( a * max_wind_speed**2
    + b * max_wind_speed
    + c)

    # Extent of storm set to 300 km 
    my_storm.storm_radius = 300000 * np.ones(my_storm.t.shape)

    my_storm.write("my_storm.storm", file_format='geoclaw')
    data.display_landfall_time = False

    
    # =======================
    #  Set Variable Friction
    # =======================
    data = rundata.friction_data

    # Variable friction
    data.variable_friction = False

    return rundata
    # end of function setgeo
    # ----------------------


if __name__ == '__main__':
    # Set up run-time parameters and write all data files.
    import sys
    if len(sys.argv) == 2:
        rundata = setrun(sys.argv[1])
    else:
        rundata = setrun()

    rundata.write()

