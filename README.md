

The Parametric Wingbox Generator
==================================

Welcome to the Parametric Wingbox Generator! This application is designed to rapidly develop and simulate wing structures.
It consists of four main modules, each building on the previous in order to generate the required geometry
and simulation data. The four modules will be explained below.


### Wing Geometry


The wing geometry consists of the foundation of the application as a whole. It has been designed bottom-up
and very carefully to ensure that the rule-based model stands up to all kinds of inputs and changes. Many
features make the wing geometry a highly customizable feature of the PWG.

* The wing geometry is formed by trapezoids, allowing the user to define whichever spans, taper, twists, or other, to define the wing planform with freedom.
* Airfoils can be placed on the planform of the wing independently of the trapezoid sections. This means that it is not mandatory to set an airfoil for each section, but you can input as little as 2 (root and tip), to as many as you need.
* The airfoils can be defined either by a ``.dat`` file (you can add your own **in Selig format** in ``./wingbox_code/input_data/airfoils``) or by defining a 4 or 5 digit airfoil either in the input Excel sheet or in the GUI.
* The inputs have been thoroughly validated so that input changes will still result in feasible results.

### AVL Analysis

The AVL analysis serves as the basis for the lift and moment calculations for the NASTRAN interface for
structural analysis. For this application, the AVL analysis has been limited to constant angle of attack,
symmetric cases for one singular set of flight characteristics (aircraft weight, speed, altitude). However,
the angle of attack can be set as a function of a specified lift coefficient.

### Wingbox Geometry


The wingbox is derived from the wing geometry and a series of structural inputs that must be specified by
the user, such as the sectional spar location, or numbers of ribs and stringers. The inputs give the user relative
flexibility to set components for each trapezoidal section. In this way, even if the distribution of ribs and
stringers is always uniform, the user can create subsections in order to locally alter a certain distribution
of elements.

### NASTRAN Analysis

The structural simulation of the wingbox is done via NASTRAN analysis, a commercial Finite Element software that can
handle complex geometries and load cases. The developed application allows the user to set the usage of tensile or
compressive strengths, different schema of component placement, material combinations and three different boundary
conditions at the wing root. It is also possible to control the quality of the mesh by assigning either a
triangular-only mesh or a mixed triangular-quadrangular mesh, as well as the minimum and maximum sizes of the element.
Note that the application cannot run NASTRAN natively; the user has to do it themselves.

How do you start the PWG?
==============================

On the root folder, you will find the input Excel sheet: ``wingbox_user_inputs.xlsx``. The input sheet will guide
you through the process of inputting data for your wing model. Remember that the input will define the initial
shape, easier to control, but modifications can always be done in the GUI. Once all of the inputs of the Excel
sheet are set, you can initialize the app by running ``AA_Initialization.py``.


    Make sure that all of the package versions specified in ``requirements.txt`` are installed in your machine
    and up to date.


    When adjusting and modifying the inputs for the wing or any of its analysis components from the ParaPy GUI,
    we recommend that you modify the inputs at the root level, as it ensures better performance of the app.


There are four sheets, one for each of the modules summarized beforehand.

### Wing Geometry


The first one deals then with the wing geometry. As mentioned above, the geometry is defined by sections,
and they should be filled up consecutively, in ascending order of the span. The root chord and root incidence
angles are specified from a so-called *Section 0*. Then, the airfoils can be input below, with no need for order.
The only conditions are that the root and tip airfoils be included.

As for the name of the airfoil, it should follows the NACA-4 or -5 digit convention (explained in the sheet), or
be one one of the names specified in the sheet itself.


    Be careful as to input the name correctly, typos will make the program raise a warning.

### Load Cases

The load cases can be customized with either a setting of desired angle of attack, or desired lift coefficient. All
load cases will be run with the same aircraft configuration. That is: weight, speed, and altitude


    When inputting the variable in the Excel sheet, you must specify exactly 'alpha' or 'CL' for each variable case
    (without the quotations).

### Wingbox Details

The wingbox inputs are very straightforward. The user has the freedom to select the location of the spars, the number
of ribs per section, and the amount of upper and lower stringers per section.

However, when interfacing toward NASTRAN some further specifications need to be established. The first of these
is the rib and skin cuts that need to be made at the trailing edge. This is done to avoid the sharp end of the
airfoil, which could cause a NASTRAN crash.

Furthermore, the cross-sections of the stringers and the rib and spar caps need to be specified. In this app
there are two ways of specifying the cross-section. The first one is by inputting the horizontal length (in the chordwise
direction (x-axis) for the stringers and spar caps, and spanwise direction (y-axis) for the rib caps) and then the
vertical length (z-axis) of an element of rectangular cross-section.

If you do not want your element to be rectangular, it is also possible to specify a cross-section by defining
the cross-section's area, horizontal axis moment of inertia (Ix or Iy), vertical axis moment of inertia (Iz), and
polar moment of inertia. This method is a bit primitive, but it allows the app to have greater flexibility in a very
simple way.


    The Excel sheet gives you flexibility when inputting dimensions. Rectangular cross-sections require two inputs,
    others require four. Make sure not to include three inputs by mistake!

Finally, the material selection. In this part you must select a material for each and every one of the components
of the wingbox. As explained in the sheet, you must name the material, temper, thickness, and testing basis. This
task is simplified by putting the available materials in a table, meaning you just have to select the combination
that suits you better.


    Make sure that the thickness that you specify is within the bounds of your material!

### Meshing Details

The final inputs by the user are the meshing details and the boundary conditions. The first input that you see is the
possibility to add your own ``.bdf`` file. This input is completely optional, and you need to specify its path. For
context, the current ``.bdf`` file. can be found at ``wingbox_code/bdf_files``.

After that is the tension/compression setting. Due to the simplicity of the application, the results will turn better
if the user specifies if the component or area where they want to focus are loaded in tension or compression. For this,
simply input a 't' or a 'c' respectively.

Then, the maximum and minimum element sizes come into play. The recommended sizes for these values are 0.1 and 0.01,
respectively, but also good results are obtained if both are set to 0.1.


    Make sure that your NASTRAN license can handle the amount of nodes generated through the element size
    specification. If you surpass the allowed node limit, increase your element sizes.

The Quad dominance parameter defines the mesh with square elements (where possible) instead of the default
triangular mesh setting. In order to activate it, input a 'Y' on its cell. If the cell is blank or has a 'N',
the default Tri mesh will be generated.

Finally, the boundary condition inputs. The wing is modelled as a cantilever beam, and as such can be clamped
at the root in four different ways. At the rib, at the root spar, at the rear spar, or a combination of the spars.
The three elements to be clamped can additionally be clamped in 6 degrees of freedom. If the user wants to specify
that the degree of freedom is clamped, they must mark the respective cell with an 'X'.


    The clamping system might be redundant at some stations. There is no need to apply a front or rear spar
    clamping in the RY DOF (rotation around the y-axis) if the rib is already clamped.