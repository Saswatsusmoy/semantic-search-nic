import pandas as pd
import sys
from tkinter import Tk, filedialog
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define input and output file paths from environment variables or use None to prompt
DEFAULT_INPUT_FILE = os.environ.get("DEFAULT_INPUT_FILE")
DEFAULT_OUTPUT_FILE = os.environ.get("DEFAULT_OUTPUT_FILE")

def clean_excel_file(file_path, output_path=None):
    """
    Clean an Excel file by removing rows where only the 'Section' column has data
    and all other columns are empty.
    
    Args:
        file_path (str): Path to the input Excel file
        output_path (str, optional): Path to save the cleaned Excel file. 
                                     If None, returns the DataFrame without saving.
    
    Returns:
        pd.DataFrame: The cleaned DataFrame
    """
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    # Check if 'Section' column exists
    if 'Section' not in df.columns:
        raise ValueError("The Excel file does not contain a 'Section' column")
    
    # Get all columns except 'Section'
    other_columns = [col for col in df.columns if col != 'Section']
    
    # Identify rows where only 'Section' has data and others are empty
    mask = df['Section'].notna() & df[other_columns].isna().all(axis=1)
    rows_to_drop = df.index[mask]
    
    # Print information about rows being dropped
    if len(rows_to_drop) > 0:
        print(f"Dropping {len(rows_to_drop)} rows where only 'Section' column has data:")
        for idx in rows_to_drop:
            print(f"  Row {idx+1}: Section = '{df.loc[idx, 'Section']}'")
    
    # Filter the DataFrame
    cleaned_df = df.drop(rows_to_drop).reset_index(drop=True)
    
    # Save to file if output_path is provided
    if output_path:
        cleaned_df.to_excel(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
    
    return cleaned_df

def select_file_with_dialog():
    """Opens a file dialog to select an Excel file."""
    root = Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select Excel File to Clean",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    root.destroy()  # Properly destroy the Tkinter window
    return file_path

def main():
    """Main function to process an Excel file."""
    # Use default paths if provided in the code
    input_file = DEFAULT_INPUT_FILE
    output_file = DEFAULT_OUTPUT_FILE
    
    # If default input path isn't set, check command line arguments
    if input_file is None:
        # If command line arguments are provided
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else output_file
        else:
            # Use dialog to select file
            print("Please select an Excel file to process...")
            input_file = select_file_with_dialog()
            if not input_file:
                print("No file selected. Exiting.")
                return
            
            # Ask if user wants to save the output
            save_response = input("Do you want to save the cleaned file? (y/n): ").lower()
            if save_response == 'y':
                root = Tk()
                root.withdraw()
                output_file = filedialog.asksaveasfilename(
                    title="Save Cleaned Excel File As",
                    filetypes=[("Excel files", "*.xlsx")],
                    defaultextension=".xlsx"
                )
                root.destroy()  # Properly destroy the Tkinter window
                if not output_file:  # If user cancels save dialog
                    output_file = None
                    print("Save cancelled. File will be processed but not saved.")
    
    try:
        # Process the file
        if not input_file:
            print("No input file specified. Exiting.")
            return
            
        df_original = pd.read_excel(input_file)
        df_cleaned = clean_excel_file(input_file, output_file)
        
        # Print summary
        rows_removed = len(df_original) - len(df_cleaned)
        print(f"\nSummary:")
        print(f"Original rows: {len(df_original)}")
        print(f"Cleaned rows: {len(df_cleaned)}")
        print(f"Rows removed: {rows_removed}")
        
        # If output file wasn't saved, show a preview of the data
        if not output_file:
            print("\nPreview of cleaned data (first 5 rows):")
            print(df_cleaned.head().to_string())
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        print(traceback.format_exc())  # Print the full stack trace for debugging

if __name__ == "__main__":
    main()
