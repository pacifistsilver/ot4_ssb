# Automating Dose-Response Experiment Generation using a GUI
## Introduction
This protocol enables a customizable and automated setup of a 2D dose-response matrix assay using the Opentrons OT-2 robot. Users can specify concentration ranges, number of replicates (maximum 3 per run), and liquid viscosity in the user interface. User-defined parameters will be translated into the Opentrons script as a configuration. Before the actual run, the reservoir carrying the corresponding components has to be set up manually. The robot will first automatically generate the specified dilution series, then distribute each component combination into the appropriate wells. Pipetting flow rates will be adjusted dynamically according to liquid viscosities to minimise pipetting errors. This provides a flexible and robust platform for investigating combinatorial effects and characterizing logic architectures.  
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
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage
Once the "opentrons" environment has been activated, you can run the below command in any suitable terminal or command line: 
   ```sh
   python main.py
   ```
This will launch the GUI. From here, you can input your parameters and generate a config file for the opentrons protocols
![Demo UI.]([https://myoctocat.com/assets/images/base-octocat.svg](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHh3bWlwcGNtbXg5cXdoaTh5OG10YjVicDdoNjZ0OWQ1ZzAyMTV1cCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KTD2jABk6gpax6Tyfs/giphy.gif))
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Authors
Code contributed by Agnes Cheung, Daniel Luo, Lihao Tao
<p align="right">(<a href="#readme-top">back to top</a>)</p>
