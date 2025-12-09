# Automating Dose-Response Experiment Generation using a GUI
## Overview
This protocol enables a customizable and automated setup of a 2D dose-response matrix assay using the Opentrons OT-2 robot. Users can specify concentration ranges, number of replicates (maximum 3 per run), and liquid viscosity in the user interface. User-defined parameters will be translated into the Opentrons script as a configuration. Before the actual run, the reservoir carrying the corresponding components has to be set up manually. The robot will first automatically generate the specified dilution series, then distribute each component combination into the appropriate wells. Pipetting flow rates will be adjusted dynamically according to liquid viscosities to minimise pipetting errors. This provides a flexible and robust platform for investigating combinatorial effects and characterizing logic architectures.  
![gif showing how the gui is operated](https://i.ibb.co/7dgk3sWT/ezgif-61e45e8e06129a0e.gif)
![gif showing how the gui is operated](https://i.ibb.co/1fXG4N2p/Untitled.jpg)
![gif showing how the gui is operated](https://i.ibb.co/278tZ8CZ/Picture1.png)
![gif showing how the gui is operated](https://i.ibb.co/mrtx2dJ2/Picture2.png)
## Prerequisites
This project relies on Conda for dependency management and environment isolation. Please ensure you have Anaconda or Miniconda installed on your system. 
### Environment Setup
1. Clone the repo
   ```sh
   git clone https://github.com/pacifistsilver/ot4_ssb.git
   ```
2. Create the environment and install dependencies
   ```sh
   conda env create -f environment.yml
   ```
3. Activate the environment
   ```sh
   conda activate opentron
   ```
### Opentrons Settings
This Opentrons script makes use of custom labware definitions: 
1. `4ti0136_96_wellplate_2200ul`.
2. `costar3370flatbottomtransparent_96_wellplate_200ul`. 

Ensure these are available in your labware directory prior to uploading your protocol, otherwise it will fail to analyse. 

We have used Opentrons API V2.0 at an apiLevel of 2.14 for the Opentrons script.
<!-- USAGE EXAMPLES -->
## Usage
1. Once the "opentrons" environment has been activated, you can run the below command in any suitable terminal or command line: 
   ```sh
   python main.py
   ```
   This will launch the GUI. From here, you can input your parameters and generate a config file for the opentrons protocols.
2. Default values are loaded initially in the "Input Parameters" tab. Any parameter can be altered under this tab, but the maximum value within the target concentration list must not exceed your inputted target concentration. 
3. In the tab "Table Preview", the dilution schedule can be viewed. 
4. If acceptable, you must click "Generate JSON". This will write a config file called `dilution_config.json` in the local directory of the `main.py` script. This is a required step.
6. Open the Opentrons GUI and set the directory of your custom labware definitions (`4ti0136_96_wellplate_2200ul` and `costar3370flatbottomtransparent_96_wellplate_200ul`) under the advanced settings tab under the Opentrons GUI settings.
7. Load this protocol and begin analysis.
8. Assuming all plates and calibrations have been set up, the script can begin execution! 
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Authors
Code contributed by Agnes Cheung, Daniel Luo, Lihao Tao
<p align="right">(<a href="#readme-top">back to top</a>)</p>
