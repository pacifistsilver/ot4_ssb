# Automating Dose-Response Experiment Generation using a GUI
## Introduction
Dose-Response experiments are notoriously labourious, especially if you are using 96 well plates plus replicates. So the main question we answer is thus: how can we automate this and make it as simple as possible for the end-user?  

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

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Authors
Code contributed by Agnes Cheung, Daniel Luo, Lihao Tao
<p align="right">(<a href="#readme-top">back to top</a>)</p>
