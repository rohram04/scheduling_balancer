🛠️ Solution: Activate Swap Space
Before you can proceed with training your ML scheduler to recognize memory pressure, you must set up and activate a swap file. This is a standard procedure in Linux system administration.

You will need administrator (root) privileges (using sudo) to run these commands.

Step 1: Create the Swap File
We will create a file to use as swap space. A size of 4GB is usually sufficient to force swapping without excessively stressing your system.

Bash

# 1. Create a 4GB file named 'swapfile'
sudo fallocate -l 4G /swapfile 
# 2. Set the correct permissions (only root should be able to read/write it)
sudo chmod 600 /swapfile
Step 2: Set up the Swap Area
You must format the file so the kernel recognizes it as a swap area.

Bash

# Tell the kernel that this file is a swap space
sudo mkswap /swapfile
Step 3: Activate the Swap File
This command turns on the swap space immediately.

Bash

# Activate the swap file
sudo swapon /swapfile
Step 4: Verify the Swap is Active
Now, check the status again. You should see your new swap file listed.

Bash

swapon --show
Example Output (Expected):

NAME      TYPE  SIZE USED PRIO
/swapfile file  4G    0B   -2
Step 5: (Optional but Recommended) Make it Permanent
To ensure the swap file is active after every reboot, add an entry to the /etc/fstab file.

Bash

# Add the following line to the end of /etc/fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab