# Bacterial Genomics Assembly Workflow Summary Dashboard

Dashboard is accessible [here](https://assembly-wf-dashboard.onrender.com)

# 1) Clone
git clone https://github.com/taylorpaisie/assembly_wf_dashboard.git
cd assembly_wf_dashboard

# 2) Create the environment (Mamba is faster, Conda also fine)
mamba env create -f environment.yml   # or: conda env create -f environment.yml
conda activate asm-dashboard

# 3) Run the app (dev)
python app.py