def process_data(file_source):
    raw_file = pd.ExcelFile(file_source)
    sheet_name = raw_file.sheet_names[0]
    
    # Safely search for the header row containing 'USER'
    preview_df = pd.read_excel(file_source, sheet_name=sheet_name, nrows=10, header=None)
    header_idx = 0
    
    for idx, row in preview_df.iterrows():
        # Convert all cell values safely to string to prevent float errors
        row_str = [str(val).upper() for val in row.values if pd.notna(val)]
        if any('USER' in val for val in row_str):
            header_idx = idx
            break

    # Read data using the detected header row
    df = pd.read_excel(file_source, sheet_name=sheet_name, header=header_idx)
    df.columns = [str(col).strip().upper() for col in df.columns]

    mapping = {}
    ordinal_cols = []
    
    for col in df.columns:
        if 'USER' in col:
            mapping[col] = 'USER'
        elif 'DISTRIBUTOR' in col:
            mapping[col] = 'Distributor'
        elif 'BEAT' in col:
            mapping[col] = 'Beat'
        elif 'PRIMARY' in col:
            mapping[col] = 'Primary Category'
        elif col == 'QTY' or 'TOTAL' in col:
            mapping[col] = 'QTY'
        elif any(ord_word in col for ord_word in ['FIRST', 'SECON', 'THIRD', 'FOURT', 'FIFTH', 'SIXTH', 'SEVENT', 'EIGHT', 'NINTH', 'TENTH']):
            ordinal_cols.append(col)

    df = df.rename(columns=mapping)

    # Convert numeric ordinal columns cleanly
    for c in ordinal_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    if 'QTY' not in df.columns or df['QTY'].sum() == 0:
        if ordinal_cols:
            df['QTY'] = df[ordinal_cols].sum(axis=1)
        else:
            num_cols = df.select_dtypes(include=['number']).columns
            df['QTY'] = df[num_cols].sum(axis=1) if len(num_cols) > 0 else 0

    # Supply default values for text fields
    for required_col, default_val in [('USER', 'Unassigned'), ('Distributor', 'Unassigned'), ('Beat', 'Unassigned'), ('Primary Category', 'General')]:
        if required_col not in df.columns:
            df[required_col] = default_val
        else:
            df[required_col] = df[required_col].fillna(default_val)

    # Clean up empty rows and numeric types
    df = df.dropna(subset=['USER', 'Distributor'], how='all')
    df['QTY'] = pd.to_numeric(df['QTY'], errors='coerce').fillna(0)
    
    return df, ordinal_cols
