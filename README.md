# RunManifest Generator for Element AVITI™ Sequencing

This is a simple and flexible Streamlit web application for generating a valid `RunManifest.csv` file used in the Element AVITI™ System. It is specifically designed for our lab that frequently runs pooled sequencing experiments with diverse library types (e.g., 10x Genomics scATAC-seq & scRNA-seq, HTO & ADT from CITE-seq) and configurations.

---

## 🔍 What is a RunManifest?

A `RunManifest.csv` file is required by the **Element AVITI™ System** and the **Bases2Fastq** software to:

- Configure sequencing runs
- Specify adapter trimming, masking, and demultiplexing parameters
- Convert bases files into demultiplexed FASTQ files based on index sequences

📘 For official documentation, refer to:  
👉 [Element Run Manifest Documentation](https://docs.elembio.io/docs/run-manifest/)

---

## 🚨 Why this tool?

In our lab, we frequently sequence **customized pooled libraries** across different lanes and sample types (e.g., RNA/GEX, ATAC, HTO, ADT). The structure of each library — including adapter lengths, index lengths, dual vs. single indexing, UMI presence, and lane assignments — often differs between runs.

Creating the RunManifest manually every time is **error-prone** and **time-consuming**, especially when:

- Pooling multiple libraries with unique index combinations across or within lanes
- Managing index length differences between 8-mer (e.g., scATAC-seq) and 10-mer (e.g., dual-index GEX/HTO) libraries
- Adjusting `I1Mask`, `I2Mask`, `UMIMask`, and `FastQMask` per lane based on library composition
- Appending the appropriate `PhiX` control sequences (8-mer vs. 10-mer, single vs. dual index) matching each lane's masking rule

This tool automatically handles all of the above and generates a validated `RunManifest_corrected.csv` in one click.

---

## ✅ Features

- Access the RunManifest Generator Web App: https://runmanifest-generator-cw9b3hxzfnpzxd6x3pgbqm.streamlit.app/
- Upload your sample sheet as `.csv`
- **Smart ATAC Index & Mask Handling (Case-Insensitive)**:
  - **Pure ATAC Lanes**: Retains native 8-mer `Index1` sequences and applies `I1Mask = I1:Y8N*` and `I2Mask = I2:N*`.
  - **Co-loaded Mixed Lanes (ATAC + GEX/HTO in the same lane)**: Automatically appends `AT` to 8-mer ATAC `Index1` sequences to match 10-mer libraries and applies `I1Mask = I1:Y*` and `I2Mask = I2:N*`.
- **Dynamic Dual-Index (`I2Mask`) Configuration**:
  - Pure GEX/HTO runs use `I2Mask = I2:Y*` across active lanes.
  - Mixed runs (e.g., Lane 1: GEX/HTO, Lane 2: ATAC) assign `I2Mask = I2:Y10N*` to GEX/HTO lanes and `I2Mask = I2:N*` to ATAC lanes.
- **Automated PhiX Spike-in Injection**: Automatically appends the 4 standard Element PhiX control entries at the end of `[SAMPLES]`, dynamically selecting between 10-mer dual-index, 8-mer dual-index, 8-mer single-index, or 10-mer single-index PhiX per lane.
- **Dynamic Lane Detection**: Automatically detects active lanes (`1`, `2`, or `1+2`) instead of hardcoding `1+2`.
- Configure `UMIMask` (`I2:Y16N*`) and `UMIFastq` settings specifically for ATAC lanes.
- Dynamically adjust `R1FastQMask` and `R2FastQMask` per lane based on sample composition.
- Output a `RunManifest_corrected.csv` fully compatible with **ElemBio Cloud (Plan a Run)** and **Bases2Fastq**.

---

## 📄 Sample Input Format

Prepare your sample sheet as a `.csv` file with the following required columns:

| SampleName  | Index1     | Index2     | Lane |
|-------------|------------|------------|------|
| ISC014_ATAC | ATTGGGAA   |            | 1    |
| ISC014_ATAC | CAGTCTGG   |            | 1    |
| ISC014_ATAC | GGCATACT   |            | 1    |
| ISC014_ATAC | TCACACTC   |            | 1    |
| ISC014_GEX  | GTAACATGCG | AGGTAACACT | 2    |
| ISC014_HTO  | CAATCCCGAC | TCCGGAATTG | 2    |

- `SampleName`: Include library keywords such as `ATAC` (case-insensitive), `GEX`, `HTO`, `ADT`, etc. (Do not include `PhiX` in your input file; it is added automatically.)
- `Index1`: i7 sequence (8-mer for ATAC or 8/10-mer for other libraries)
- `Index2`: i5 sequence (required for dual-indexed libraries like GEX/HTO; leave blank for ATAC)
- `Lane`: Lane number (`1` or `2`)

📝 **Note on ATAC 8-mer Index1**: If an ATAC sample is in its own dedicated lane, its 8-mer `Index1` is kept as-is with `I1:Y8N*`. If it shares the same lane with non-ATAC (10-mer) samples, `AT` is automatically appended to convert it into a 10-mer sequence.
