import os

import numpy as np
import matplotlib.pyplot as plt

import clawpack.visclaw.colormaps as colormap
import clawpack.visclaw.gaugetools as gaugetools
import clawpack.clawutil.data as clawutil
import clawpack.amrclaw.data as amrclaw
import clawpack.geoclaw.data as geodata


import clawpack.geoclaw.surge.plot as surgeplot

try:
    from setplotfg import setplotfg
except:
    setplotfg = None

# def gauge_topo(cd, dry_tolerance=1e-16, topo_index=None):
#     """"""
#     if not topo_index:
#         # Assumes that topo is in the first location in aux
#         topo_index = 4 + 0
#     return cd.gaugesoln.q[topo_index, :]

# def gauge_wind(cd, dry_tolerance=1e-16, wind_index=None):
#     """"""
#     if not wind_index:
#         # Assumes that all aux fields were written out
#         wind_index = 4 + wind_field 
#     return np.sqrt(cd.gaugesoln.q[wind_index, :]**2 + 
#                    cd.gaugesoln.q[wind_index + 1, :]**2)


# def gauge_pressure(cd, dry_tolerance=1e-16, pressure_index=None):
#     """"""
#     if not pressure_index:
#         # Assumes that all aux fields were written out
#         pressure_index = 4 + pressure_field 
#     return cd.gaugesoln.q[pressure_index, :]


def setplot(plotdata=None):
    """"""

    if plotdata is None:
        from clawpack.visclaw.data import ClawPlotData
        plotdata = ClawPlotData()

    # clear any old figures,axes,items data
    plotdata.clearfigures()
    plotdata.format = 'binary'

    # Load data from output
    clawdata = clawutil.ClawInputData(2)
    clawdata.read(os.path.join(plotdata.outdir, 'claw.data'))
    physics = geodata.GeoClawData()
    physics.read(os.path.join(plotdata.outdir, 'geoclaw.data'))
    surge_data = geodata.SurgeData()
    surge_data.read(os.path.join(plotdata.outdir, 'surge.data'))
    friction_data = geodata.FrictionData()
    friction_data.read(os.path.join(plotdata.outdir, 'friction.data'))

    # Load storm track
    # track_path = os.path.join(plotdata.outdir, 'fort.track')
    # print("This is the track path: " + track_path)
    track = surgeplot.track_data(os.path.join(plotdata.outdir, 'fort.track'))



    # Set afteraxes function
    def surge_afteraxes(cd):
        surgeplot.surge_afteraxes(cd, track, plot_direction=False,
                                             kwargs={"markersize": 4})

    # Color limits
    surface_limits = [-5.0, 5.0]
    speed_limits = [0.0, 3.0]
    wind_limits = [0, 64]
    pressure_limits = [935, 1013]
    friction_bounds = [0.01, 0.04]

    # Center of domain
    x = (clawdata.upper[0] - clawdata.lower[0]) / 2 + clawdata.lower[0]
    y = (clawdata.upper[1] - clawdata.lower[1]) / 2 + clawdata.lower[1]

    def friction_after_axes(cd):
        plt.title(r"Manning's $n$ Coefficient")

    # ==========================================================================
    #   Plot specifications
    # ==========================================================================
    regions = {"Full": {"xlimits": (clawdata.lower[0], clawdata.upper[0]),
                        "ylimits": (clawdata.lower[1], clawdata.upper[1]),
                        "figsize": (6.4, 4.8)},
               "Zoom": {"xlimits": (x - 2, x + 2), 
                        "ylimits": (y - 2, y + 2),
                        "figsize": (6.4, 4.8)},}

    for (i, (name, region_dict)) in enumerate(regions.items()):

        # Surface Figure
        plotfigure = plotdata.new_plotfigure(name=f"Surface - {name}", figno=1+i)
        plotfigure.kwargs = {"figsize": region_dict['figsize']}
        plotaxes = plotfigure.new_plotaxes()
        plotaxes.title = "Surface"
        plotaxes.xlimits = region_dict["xlimits"]
        plotaxes.ylimits = region_dict["ylimits"]
        plotaxes.afteraxes = surge_afteraxes

        surgeplot.add_surface_elevation(plotaxes, bounds=surface_limits)
        surgeplot.add_land(plotaxes, bounds=[0.0, 20.0])
        plotaxes.plotitem_dict['surface'].amr_patchedges_show = [1] * 10
        plotaxes.plotitem_dict['land'].amr_patchedges_show = [1] * 10
        # plotaxes.plotitem_dict['surface'].amr_celledges_show = [1] * 10
        # plotaxes.plotitem_dict['land'].amr_celledges_show = [1] * 10

        # Speed Figure
        plotfigure = plotdata.new_plotfigure(name="Currents - %s" % name)
        plotfigure.kwargs = {"figsize": region_dict['figsize']}
        plotaxes = plotfigure.new_plotaxes()
        plotaxes.title = "Currents"
        plotaxes.xlimits = region_dict["xlimits"]
        plotaxes.ylimits = region_dict["ylimits"]
        plotaxes.afteraxes = surge_afteraxes

        surgeplot.add_speed(plotaxes, bounds=speed_limits)
        surgeplot.add_land(plotaxes, bounds=[0.0, 20.0])
        plotaxes.plotitem_dict['speed'].amr_patchedges_show = [0] * 10
        plotaxes.plotitem_dict['land'].amr_patchedges_show = [0] * 10

    #
    #  Hurricane Forcing fields
    #
    # Pressure field
    plotfigure = plotdata.new_plotfigure(name='Pressure')
    plotfigure.show = surge_data.pressure_forcing and True

    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = regions['Full']['xlimits']
    plotaxes.ylimits = regions['Full']['ylimits']
    plotaxes.title = "Pressure Field"
    plotaxes.afteraxes = surge_afteraxes
    plotaxes.scaled = True
    surgeplot.add_pressure(plotaxes, bounds=pressure_limits)
    surgeplot.add_land(plotaxes, bounds=[0.0, 20.0])

    # Wind field
    plotfigure = plotdata.new_plotfigure(name='Wind Speed')
    plotfigure.show = surge_data.wind_forcing and True

    plotaxes = plotfigure.new_plotaxes()
    plotaxes.xlimits = regions['Full']['xlimits']
    plotaxes.ylimits = regions['Full']['ylimits']
    plotaxes.title = "Wind Field"
    plotaxes.afteraxes = surge_afteraxes
    plotaxes.scaled = True
    surgeplot.add_wind(plotaxes, bounds=wind_limits)
    surgeplot.add_land(plotaxes, bounds=[0.0, 20.0])

    # ========================================================================
    #  Figures for gauges
    # ========================================================================
    # plotfigure = plotdata.new_plotfigure(name='Gauge Surfaces', figno=300,
    #                                      type='each_gauge')
    # plotfigure.show = True
    # plotfigure.clf_each_gauge = True

    # plotaxes = plotfigure.new_plotaxes()
    # plotaxes.time_scale = 1 / (24 * 60**2)
    # plotaxes.grid = True
    # plotaxes.xlimits = [0, 4]
    # plotaxes.ylimits = 'auto'
    # plotaxes.title = "Surface"
    # plotaxes.ylabel = "Surface (m)"
    # plotaxes.time_label = "Days relative to landfall"
    
    # plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    # plotitem.plot_var = surgeplot.gauge_surface
    # # Plot red area if gauge is dry
    # plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    # plotitem.plot_var = surgeplot.gauge_dry_regions
    # plotitem.kwargs = {"color":'lightcoral', "linewidth":5}

    # === Gauge Wind
    plotfigure = plotdata.new_plotfigure(name='Gauge Wind Speed',
                                         type='each_gauge', figno=476)
    plotfigure.show = True
    plotfigure.clf_each_gauge = True

    plotaxes = plotfigure.new_plotaxes()
    plotaxes.time_scale = 1 / (24 * 60**2)
    plotaxes.grid = True
    plotaxes.xlimits = [0, 4]
    plotaxes.ylimits = 'auto'
    plotaxes.title = "Wind Speed"
    plotaxes.ylabel = "Speed (m/s)"
    plotaxes.time_label = "Days relative to landfall"
    
    plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    plotitem.plot_var = lambda cd: surgeplot.gauge_wind(cd, wind_index=5)

    # === Gauge Pressure
    plotfigure = plotdata.new_plotfigure(name='Gauge Pressure',
                                         type='each_gauge', figno=477)
    plotfigure.show = True
    plotfigure.clf_each_gauge = True

    plotaxes = plotfigure.new_plotaxes()
    plotaxes.time_scale = 1 / (24 * 60**2)
    plotaxes.grid = True
    plotaxes.xlimits = [0, 4]
    plotaxes.ylimits = 'auto'
    plotaxes.title = "Pressure"
    plotaxes.ylabel = "Pressure (kPa)"
    plotaxes.time_label = "Days relative to landfall"
    
    plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    plotitem.plot_var = lambda cd: surgeplot.gauge_pressure(cd, pressure_index=7)

    # === Gauge Bathy
    plotfigure = plotdata.new_plotfigure(name='Gauge Bathy',
                                         type='each_gauge', figno=478)
    plotfigure.show = True
    plotfigure.clf_each_gauge = True

    plotaxes = plotfigure.new_plotaxes()
    plotaxes.time_scale = 1 / (24 * 60**2)
    plotaxes.grid = True
    plotaxes.xlimits = [0, 4]
    plotaxes.ylimits = 'auto'
    plotaxes.title = "Topography"
    plotaxes.ylabel = "Topography (m)"
    plotaxes.time_label = "Days relative to landfall"

    plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    plotitem.plot_var = surgeplot.gauge_topo

    # =====================
    #  Gauge Location Plot
    # =====================
    def gauge_location_afteraxes(cd):
        plt.subplots_adjust(left=0.12, bottom=0.06, right=0.97, top=0.97)
        surge_afteraxes(cd)
        gaugetools.plot_gauge_locations(cd.plotdata, gaugenos='all',
                                        format_string='ko', add_labels=False)

    plotfigure = plotdata.new_plotfigure(name="Gauge Locations", figno=548)
    plotfigure.show = True

    # Set up for axes in this figure:
    plotaxes = plotfigure.new_plotaxes()
    plotaxes.title = 'Gauge Locations'
    plotaxes.scaled = True
    plotaxes.xlimits = [x - 1.25, x + 1.25]
    plotaxes.ylimits = [y - 1.25, y + 1.25]
    plotaxes.afteraxes = gauge_location_afteraxes
    surgeplot.add_surface_elevation(plotaxes, bounds=surface_limits)
    surgeplot.add_land(plotaxes, bounds=[0.0, 20.0])
    plotaxes.plotitem_dict['surface'].amr_celledges_show = [1] * 10
    plotaxes.plotitem_dict['land'].amr_celledges_show = [1] * 10
    # plotaxes.plotitem_dict['surface'].amr_patchedges_show = [1] * 10
    # plotaxes.plotitem_dict['land'].amr_patchedges_show = [0] * 10

    # -----------------------------------------
    # Parameters used only when creating html and/or latex hardcopy
    # e.g., via pyclaw.plotters.frametools.printframes:

    plotdata.printfigs = True                # print figures
    plotdata.print_format = 'png'            # file format
    plotdata.print_framenos = 'all'          # list of frames to print
    # plotdata.print_framenos = 'none'          # list of frames to print
    plotdata.print_gaugenos = 'all'
    # plotdata.print_fignos = 'all'            # list of figures to print
    plotdata.print_fignos = [1, 2, 548, 300, 476, 477, 478, 479]
    plotdata.html = True                     # create html files of plots?
    plotdata.latex = True                    # create latex file of plots?
    plotdata.latex_figsperline = 2           # layout of plots
    plotdata.latex_framesperline = 1         # layout of plots
    plotdata.latex_makepdf = False           # also run pdflatex?
    plotdata.parallel = True                 # parallel plotting

    return plotdata
