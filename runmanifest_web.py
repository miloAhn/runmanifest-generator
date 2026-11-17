import pandas as pd
import os
import tempfile
import streamlit as st

def process_samples(df, output_dir):
    # Clean whitespace in string columns
    df['SampleName'] = df['SampleName'].astype(str).str.strip()
    df['Index1'] = df['Index1'].astype(str).str.strip()
    if 'Index2' in df.columns:
        df['Index2'] = df['Index2'].fillna('').astype(str).str.strip()
    else:
        df['Index2'] = ''
    df['Lane'] = df['Lane'].astype(str).str.strip()

    # If only a single lane identifier is used (e.g., all "1"), convert all to "1+2" for standard single-pool flowcell runs
    unique_lanes = df['Lane'].unique()
    if len(unique_lanes) == 1:
        df['Lane'] = "1+2"

    # Get sorted unique lanes (will be ["1+2"] for single-pool, or ["1", "2"] for split-lane runs)
    lanes = sorted(df['Lane'].unique())
    
    # Identify ATAC-specific lanes (case-insensitive)
    is_atac_row = df['SampleName'].str.contains("ATAC", case=False, na=False)
    atac_lanes = sorted(df[is_atac_row]['Lane'].unique())
    
    # Check each lane to see if ATAC and non-ATAC samples coexist in the same pool/lane
    mixed_within_lane = {}
    for lane in lanes:
        lane_df = df[df['Lane'] == lane]
        has_atac = lane in atac_lanes
        has_non_atac = (~lane_df['SampleName'].str.contains("ATAC", case=False, na=False)).any()
        mixed_within_lane[lane] = (has_atac and has_non_atac)
        
        if mixed_within_lane[lane]:
            # 1) Append 'AT' to 8-mer ATAC to match 10-mer GEX/HTO in the same lane
            mask_atac_8 = (df['Lane'] == lane) & is_atac_row & (df['Index1'].str.len() == 8)
            df.loc[mask_atac_8, 'Index1'] = df.loc[mask_atac_8, 'Index1'] + "AT"
            
            # 2) Clear Index2 for ALL samples in this lane because I2Mask must be I2:N*
            df.loc[df['Lane'] == lane, 'Index2'] = ''

    # Initialize common SETTINGS section
    settings = [
        ["SettingName", "Value", "Lane"],
        ["R1Adapter", "AAAAAAAAAAAAAAAAAAA", "1+2"],
        ["R1AdapterTrim", "FALSE", "1+2"],
        ["R2Adapter", "TTTTTTTTTTTTTTTTTTT", "1+2"],
        ["R2AdapterTrim", "FALSE", "1+2"]
    ]

    # Configure I1Mask and I2Mask
    if len(atac_lanes) == 0:
        # Pure GEX/HTO across the entire flowcell
        settings.append(["I1Mask", "I1:Y*", "1+2"])
        settings.append(["I2Mask", "I2:Y*", "1+2"])
    elif len(atac_lanes) == len(lanes):
        # Every lane contains ATAC (either single-pool "1+2" with ATAC, or both "1" and "2" have ATAC)
        if not any(mixed_within_lane.values()):
            settings.append(["I1Mask", "I1:Y8N*", "1+2"])
        elif all(mixed_within_lane.values()):
            settings.append(["I1Mask", "I1:Y*", "1+2"])
        else:
            for lane in lanes:
                i1_val = "I1:Y*" if mixed_within_lane[lane] else "I1:Y8N*"
                settings.append(["I1Mask", i1_val, str(lane)])
        settings.append(["I2Mask", "I2:N*", "1+2"])
    else:
        # Split-lane run where one lane is pure GEX/HTO and the other has ATAC
        for lane in lanes:
            if lane in atac_lanes:
                i1_val = "I1:Y*" if mixed_within_lane[lane] else "I1:Y8N*"
                settings.append(["I1Mask", i1_val, str(lane)])
                settings.append(["I2Mask", "I2:N*", str(lane)])
            else:
                settings.append(["I1Mask", "I1:Y*", str(lane)])
                lane_df = df[df['Lane'] == lane]
                i2_val = "I2:Y8N*" if (lane_df['Index2'].str.len() == 8).all() else "I2:Y10N*"
                settings.append(["I2Mask", i2_val, str(lane)])

    # Add FastQ generation flags for Index reads
    settings.append(["I1FastQ", "TRUE", "1+2"])
    settings.append(["I2FastQ", "TRUE", "1+2"])

    # Add UMI-specific settings for ATAC lanes (will be "1+2" if single-pool)
    for lane in atac_lanes:
        settings.append(["UMIMask", "I2:Y16N*", str(lane)])
        settings.append(["UMIFastq", "TRUE", str(lane)])
    
    # Configure R1/R2 FastQMask depending on ATAC presence
    if len(atac_lanes) == 0 or (len(atac_lanes) == len(lanes) and not any(mixed_within_lane.values())):
        settings.append(["R1FastQMask", "R1:Y*", "1+2"])
        settings.append(["R2FastQMask", "R2:Y*", "1+2"])
    elif len(atac_lanes) == len(lanes) and all(mixed_within_lane.values()):
        settings.append(["R1FastQMask", "R1:Y*", "1+2"])
        settings.append(["R2FastQMask", "R2:Y*", "1+2"])
    else:
        for lane in lanes:
            if lane in atac_lanes:
                settings.append(["R1FastQMask", "R1:Y*", str(lane)])
                if mixed_within_lane[lane]:
                    settings.append(["R2FastQMask", "R2:Y*", str(lane)])
                else:
                    settings.append(["R2FastQMask", "R2:Y49N*", str(lane)])
            else:
                settings.append(["R1FastQMask", "R1:Y28N*", str(lane)])
                settings.append(["R2FastQMask", "R2:Y*", str(lane)])

    # Define PhiX sequences
    phix_dual_10 = [
        ("ATGTCGCTAG", "CTAGCTCGTA"),
        ("CACAGATCGT", "ACGAGAGTCT"),
        ("GCACATAGTC", "GACTACTAGC"),
        ("TGTGTCGACA", "TGTCTGACAG")
    ]
    phix_dual_8 = [
        ("ATGTCGCT", "CTAGCTCG"),
        ("CACAGATC", "ACGAGAGT"),
        ("GCACATAG", "GACTACTA"),
        ("TGTGTCGA", "TGTCTGAC")
    ]
    phix_single_8 = [
        ("ATGTCGCT", ""),
        ("CACAGATC", ""),
        ("GCACATAG", ""),
        ("TGTGTCGA", "")
    ]
    phix_single_10 = [
        ("ATGTCGCTAG", ""),
        ("CACAGATCGT", ""),
        ("GCACATAGTC", ""),
        ("TGTGTCGACA", "")
    ]

    def get_dual_phix_for_df(sub_df):
        if (sub_df['Index1'].str.len() == 8).all():
            return phix_dual_8
        return phix_dual_10

    # Save final RunManifest
    output_path = os.path.join(output_dir, "RunManifest_corrected.csv")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[SETTINGS],,,\n")
        for row in settings:
            f.write(",".join(row) + "\n")
        f.write("[SAMPLES],,,\n")
        
        # Write user-uploaded samples (Lane column is now "1+2" if single-pool)
        df.to_csv(f, index=False)
        
        # Add PhiX samples dynamically
        if len(atac_lanes) == 0:
            phix_list = get_dual_phix_for_df(df)
            for idx1, idx2 in phix_list:
                f.write(f"PhiX,{idx1},{idx2},1+2\n")
        elif len(atac_lanes) == len(lanes) and not any(mixed_within_lane.values()):
            for idx1, idx2 in phix_single_8:
                f.write(f"PhiX,{idx1},{idx2},1+2\n")
        elif len(atac_lanes) == len(lanes) and all(mixed_within_lane.values()):
            for idx1, idx2 in phix_single_10:
                f.write(f"PhiX,{idx1},{idx2},1+2\n")
        else:
            for lane in lanes:
                lane_df = df[df['Lane'] == lane]
                if lane in atac_lanes:
                    phix_list = phix_single_10 if mixed_within_lane[lane] else phix_single_8
                    for idx1, idx2 in phix_list:
                        f.write(f"PhiX,{idx1},{idx2},{lane}\n")
                else:
                    phix_list = get_dual_phix_for_df(lane_df)
                    for idx1, idx2 in phix_list:
                        f.write(f"PhiX,{idx1},{idx2},{lane}\n")

    return output_path

# --- Streamlit Web Interface ---
st.title("🧬 MiloAhn's RunManifest Generator")

uploaded_file = st.file_uploader("Upload your sample sheet (.csv)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded. Generating RunManifest...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = process_samples(df, tmpdir)
        with open(output_path, "rb") as f:
            st.download_button("📥 Download RunManifest", f, file_name="RunManifest_corrected.csv", mime="text/csv")
