# How to use the QMC Summer School Virtual Machine

QMC can be easily tried out using the virtual machine provided here. It contains QMCPACK, Quantum ESPRESSO, and PySCF, as well as
all the summer school files. The virtual machine provides a familiar desktop GUI environment with no risk of interference with other
installed software. The installation scripts are provided and can be used as inspiration for a direct installation. For example, you
could directly run them on Windows in an Ubuntu/WSL2 terminal.

For any use of the virtual machine beyond the summer school, we recommend changing the password. For longer term use of QMCPACK and
for higher performance, we recommend installing it directly.

## x86-based Windows, Linux, and macOS

* Install the latest version of VirtualBox (free, no cost) from
  https://www.virtualbox.org/  . We used v7.1.10 to make the image. 
* Download the image file from https://bit.ly/qmcsummerschool2025vbximage . The
  file is around 6GB in size, so will take several minutes to download even on
  the fastest networks, and potentially several hours. Be patient and try again
  at a different time or using a different network if initially unsuccessful.
* Run VirtualBox and import the image to setup the virtual machine:
 * In VirtualBox, select the menu File->Import Appliance. Import the QMCSummerSchool2025Image.ova that was just downloaded.
 * Customize the "Appliance" Settings during Import to suit your computer. e.g. Increase the CPU count to match the machine you are running on (maybe 4 for laptop, 16-128 for a workstation), Increase the memory (8GB should be OK on laptops).  Not setting the core count and memory sufficiently large will result in poor performance. Consider renaming the machine.
 * Complete importing the virtual machine. Initial setup may take a few minutes.
 * In the main VirtualBox window select the new machine, then "Start". You should see Ubuntu boot and a standard desktop appear.
 * The virtual machine is setup to automatically log in as user "qmcuser". Should you need to authenticate the word you need is "qmc2025" (without quotes).
 * You can get a terminal (or other application) by clicking the dotted circle icon at the bottom left and either typing or selecting the application you want.
 * Inside a terminal, e.g. "qmcpack", "qmcpack_complex", "pw.x" are on the path. NEXUS and PySCF are available through python. These are installed in $HOME/apps
 * You can install any standard Linux software, e.g. via "sudo apt-get install your_favorite_editor".

## Apple Silicon based macOS machines

We provide a virtual machine for UTM, an open source virtualization and
emulation package. Ubuntu Linux for ARM is virtualized and runs at close to full
speed on Apple Silicon. The virtual machine uses Ubuntu 25.04 for compatibility.

* Install the latest version of UTM for mac (free, open source) from https://mac.getutm.app . You
  can also purchase from the Mac App Store to contribute financially to the
  project.
* Download the image file from https://bit.ly/qmcsummerschool2025utmimage . The
  file is around 6GB in size, so will take several minutes to download even on the
  fastest networks, and potentially several hours. Be patient and try again at a
  different time or using a different network if initially unsuccessful.
* Unzip the downloaded compressed image file to obtain QMCSummerSchool2025Image.utm
* In UTM, select "Create a New Virutal Machine", then "Open..." an existing machine. Import the downloaded QMCSummerSchool2025Image.utm file
* Start the newly created virtual machine using the large "play" icon
* The virtual machine is setup to automatically log in as user "qmcuser". Should you need to authenticate the word you need is "qmc2025" (without quotes).
* You can get a terminal (or other application) by clicking the dotted circle icon at the bottom left and either typing or selecting the application you want.
* Inside a terminal, e.g. "qmcpack", "qmcpack_complex", "pw.x"are on the path.
  NEXUS and PySCF are available through python. These were installed in
  $HOME/apps.
* You can install any standard Linux software, e.g. via "sudo apt-get install your_favorite_editor".

# Instructions for building the QMC virtual machines

These instructions allow either recreating the exact virtual machine and
image used in the summer school or the production of a customized version.

**Important: Do not freelance any activities involving passwords or access
  tokens (etc.) while making a virtual machine because they may be recoverable from the
  image file.**

## VirtualBox on x86 machines

The virtual machine image for the summer school is currently created "by hand", but once proven out the intent is to fully automate
creation of the image so that a "live" distribution of QMCPACK can be provided.

* Download Ubuntu 24.04 LTS base image http://www.releases.ubuntu.com/24.04/
* Create new machine in VirtualBox
  * Use 8GB memory, variable 20GB hard drive
* Before initial start:
  * Set maximum video memory 128MB to avoid black screen on resize
  * Set 4 CPUs, not default 1. For the school we assume an at least 4 core setup.
* Start the VM and work through the Ubuntu installer:
  * Set US Keyboard
  * Minimal installation
  * Download updates during install
  * Don't install 3rd party software
  * Erase disk and install Ubuntu
  * Set New York time

* name: QMCVM
* computer name: QMCVM
* username: qmcuser
* magic word: qmc2025
* **set login automatically**
* (Standard install questions... long wait + reboot)
* Allow software updater to run and reboot as needed
* Settings (at top right) ->Privacy->Screen Lock disable

* In terminal
```
# Expect the install to take a few hours
# Install script uses sudo in the beginning
# will need password input if not run before
cd $HOME
sudo apt-get -y install git
git clone https://github.com/QMCPACK/qmc_summer_school_2025.git
cd qmc_summer_school_2025/virtual_machine
nohup ./ubuntu_setup.sh >& out&
tail -f out
```
* There are customization options in the setup script to enable or disable
  different applications.
* Reboot when finished (Due to updates+required kernel extensions for Guest additions)
* Devices->Install Guest Additions CD. Install integrations.
* Reboot
* Check `which qmcpack` works
* VirtualBox Image compression (RECOMMENDED TO REDUCE SIZE)
  * In a Terminal `dd if=/dev/zero of=/var/tmp/bigemptyfile bs=4096k ; rm /var/tmp/bigemptyfile`
  * shutdown VM
  * `VBoxManage modifymedium --compact /path/to/thedisk.vdi`
  * e.g. `VBoxManage modifymedium --compact /Users/pk7/VirtualBox\ VMs/WorkshopUbuntu/WorkshopUbuntu.vdi` or `vboxmanage` with Linux hosts (capitalization varies)
* Export image using VirtualBox. Set title, URL etc.

## UTM on Apple Silicon machines

* Install the latest version of UTM from https://mac.getutm.app/ (currently 2.4.1)
* Download the Ubuntu 25.04 from https://cdimage.ubuntu.com/releases/plucky/release/ e.g. https://cdimage.ubuntu.com/releases/plucky/release/ubuntu-25.04-desktop-arm64.iso
* In UTM:
  * Create New Virtual Machine 
    * Information: Name: QMCVM, Style: OS
    * System: Architecture ARM64 (aarch64), Memory: 8192 MB
  * Select QMCVM. Before starting, select CD/DVD, browse and set to
    downloaded ubuntu-25.04-desktop-arm64.iso
  * Start VM (large "play" button)
    * Select Ubuntu
    * Run Install Ubuntu when desktop appears
      * Minimal installation, download updates while installing
      * Erase disk and install ubuntu
      * name: QMCVM
      * computer name: QMCVM
      * username: qmcuser
      * magic word: qmc2025
      * **set login automatically**
      * (Standard install questions... long wait + reboot)
      * Allow software updater to run and reboot as needed
      * Settings (at top right) ->Privacy->Screen Lock disable
      * In terminal
      ```
      # Expect the install to take a few hours
      # Install script uses sudo in the beginning
      # will need password input if not run before
      cd $HOME
      sudo apt-get -y install git
      git clone https://github.com/QMCPACK/qmc_summer_school_2025.git
      cd qmc_summer_school_2025/virtual_machine
      nohup ./ubuntu_setup.sh >& out&
      tail -f out
      ```
      * There are customization options in the setup script to enable or disable
  different applications. 
      * Reboot after successful installation.
      * Check `which qmcpack` works
      * Power Off the VM
      * Clear the CD/DVD with the .iso
      * "Share" the VM, Save As QMCSummerSchool2025Image.utm
      * Compress (ZIP) the image to reduce the ~16GB image file size to ~6GB.
