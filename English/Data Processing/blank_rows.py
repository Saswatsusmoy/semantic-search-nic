import pandas as pd
import os

def remove_blank_rows(input_file, output_file=None):
    # If no output file is specified, create one with "_cleaned" appended to the filename
    if output_file is None:
        file_name, file_ext = os.path.splitext(input_file)
        output_file = f"{file_name}_cleaned{file_ext}"
    
    # Read the Excel file
    df = pd.read_excel(input_file)
    
    # Remove blank rows (rows where all values are NaN)
    df_cleaned = df.dropna(how='all')
    
    # Save the cleaned dataframe to a new Excel file
    df_cleaned.to_excel(output_file, index=False)
    
    print(f"Processed file: {input_file}")
    print(f"Removed {len(df) - len(df_cleaned)} blank rows")
    print(f"Saved cleaned file as: {output_file}")
    
    return output_file

if __name__ == "__main__":
    # Replace this with your Excel file path
    input_excel_file = "C:/Users/saswa/Downloads/Final NIC_Codes_processed.xlsx"
    
    # Call the function to remove blank rows
    remove_blank_rows(input_excel_file)