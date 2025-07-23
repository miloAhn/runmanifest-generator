# RunManifest Generator for Element AVITI™ Sequencing

This is a simple and flexible Streamlit web application for generating a valid `RunManifest.csv` file used in the Element AVITI™ System. It is specifically designed for our lab that frequently run pooled sequencing experiments with diverse library types(e.g. 10X scATAC-seq & scRNA-seq, HTO & ADT from CITE-seq)  and configurations.

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

In our lab, we frequently sequence **customized pooled libraries** across different lanes and sample types (e.g. RNA, ATAC, HTO, ADT). The structure of each library — including adapter lengths, index lengths, UMI presence, and lane assignments — often differs between runs.

Creating the RunManifest manually every time is **error-prone** and **time-consuming**, especially when:

- Pooling multiple libraries with unique index combinations
- Distinguishing between 8-mer and 10-mer index sequences (e.g. ATAC index1 requires `AT` appended to 8-mers)
- Adjusting `UMIMask`, `FastQMask`, or lane-specific settings based on library type

This tool automatically handles all of the above and generates a valid `RunManifest.csv` in one click.

---

## ✅ Features

- Access the RunManifest Generator Web App https://runmanifest-generator-cw9b3hxzfnpzxd6x3pgbqm.streamlit.app/
- Upload your sample sheet as `.csv`
- Automatically detect **ATAC** samples and append `AT` to 8-mer Index1 sequences
- Configure `UMIMask` and `UMIFastq` settings only for ATAC lanes
- Dynamically adjust `FastQMask` per lane based on sample composition
- Output a `RunManifest_corrected.csv` fully compatible with **Bases2Fastq**

---

## 📄 Sample Input Format

Prepare your sample sheet as a `.csv` file with the following required columns:

| SampleName     | Index1     | Index2     | Lane   |
|----------------|------------|------------|--------|
| ISC014_ATAC    | ATTGGGAA   |            |   1    |
| ISC014_ATAC    | CAGTCTGG   |            |   1    |
| ISC014_ATAC    | GGCATACT   |            |   1    |
| ISC014_ATAC    | TCACACTC   |            |   1    |
| ISC014_GEX     | GTAACATGCG |            |   2    | 
| ISC014_HTO     | CAATCCCGAC |            |   2    |

- `SampleName`: Must include keywords like `ATAC`, `GEX`, `HTO`, `ADT`, etc.
- `Lane`: Lane number (usually 1 or 2)
- `Index1`: i7 sequence (8-mer or 10-mer; if 8-mer for ATAC, `AT` will be auto-appended)
- `Index2`: i5 sequence (optional but recommended for demultiplexing)

📝 ATAC samples with 8-mer `Index1` values will be automatically converted to 10-mer by appending `AT`.


