import pandas as pd
import os
import tempfile
import streamlit as st

def process_samples(df, output_dir):
    # Get all unique lanes
    lanes = df['Lane'].unique()
    
    # Identify ATAC-specific lanes
    atac_lanes = sorted(df[df['SampleName'].str.contains("ATAC", na=False)]['Lane'].unique())

    # For ATAC samples with 8-mer Index1, append 'AT' to make 10-mer
    is_atac = df['SampleName'].str.contains("ATAC", na=False)
    is_8mer = df['Index1'].str.len() == 8
    df.loc[is_atac & is_8mer, 'Index1'] = df.loc[is_atac & is_8mer, 'Index1'] + "AT"
    
    # Initialize SETTINGS section
    settings = [
        ["SettingName", "Value", "Lane"],
        ["R1Adapter", "AAAAAAAAAAAAAAAAAAA", "1+2"],
        ["R1AdapterTrim", "FALSE", "1+2"],
        ["R2Adapter", "TTTTTTTTTTTTTTTTTTT", "1+2"],
        ["R2AdapterTrim", "FALSE", "1+2"],
        ["I1Mask", "I1:Y*", "1+2"],
        ["I2Mask", "I2:N*", "1+2"],
        ["I1FastQ", "TRUE", "1+2"],
        ["I2FastQ", "TRUE", "1+2"]
    ]

    # Add UMI-specific settings for ATAC lanes
    for lane in atac_lanes:
        settings.append(["UMIMask", "I2:Y16N*", str(lane)])
        settings.append(["UMIFastq", "TRUE", str(lane)])
    
    # Configure R1/R2 FastQMask depending on ATAC presence
    if len(atac_lanes) == 0 or len(atac_lanes) == len(lanes):
        settings.append(["R1FastQMask", "R1:Y*", "1+2"])
        settings.append(["R2FastQMask", "R2:Y*", "1+2"])
    else:
        for lane in lanes:
            if lane in atac_lanes:
                # If non-ATAC samples exist in the same lane, use full R2 mask
                other_samples_exist = df[(df['Lane'] == lane) & ~df['SampleName'].str.contains("ATAC", na=False)].shape[0] > 0
                settings.append(["R1FastQMask", "R1:Y*", str(lane)])
                if other_samples_exist:
                    settings.append(["R2FastQMask", "R2:Y*", str(lane)])
                else:
                    settings.append(["R2FastQMask", "R2:Y49N*", str(lane)])
            else:
                settings.append(["R1FastQMask", "R1:Y28N*", str(lane)])
                settings.append(["R2FastQMask", "R2:Y*", str(lane)])

    # Save final RunManifest
    output_path = os.path.join(output_dir, "RunManifest_corrected.csv")
    with open(output_path, "w") as f:
        f.write("[SETTINGS],,,\n")
        for row in settings:
            f.write(",".join(row) + "\n")
        f.write("[SAMPLES],,,\n")
        
        # Write the user-uploaded samples first
        df.to_csv(f, index=False)
        
        # --- MODIFICATION START ---
        # Add static PhiX samples at the end of the [SAMPLES] section
        f.write("PhiX,ATGTCGCTAG,,1+2\n")
        f.write("PhiX,CACAGATCGT,,1+2\n")
        f.write("PhiX,GCACATAGTC,,1+2\n")
        f.write("PhiX,TGTGTCGACA,,1+2\n")
        # --- MODIFICATION END ---

    return output_path

# --- Streamlit Web Interface ---
st.title("🧬 MiloAhn's RunManifest Generator (with ATAC 8-mer Index auto-fix)")

uploaded_file = st.file_uploader("Upload your sample sheet (.csv)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded. Generating RunManifest...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = process_samples(df, tmpdir)
        with open(output_path, "rb") as f:
            st.download_button("📥 Download RunManifest", f, file_name="RunManifest_corrected.csv", mime="text/csv")
