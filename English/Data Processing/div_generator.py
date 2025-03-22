import pandas as pd
import os

def process_division_groups(file_path, output_path=None):
    """
    Process Excel file to extract digits from 'Group' column and update 'Divison' column.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Check if required columns exist
        if 'Divison' not in df.columns or 'Group' not in df.columns:
            print("Error: Required columns 'Divison' and 'Group' not found in the Excel file.")
            return None
        
        # Process each row
        for index, row in df.iterrows():
            # Convert Group value to string and check if it contains digits
            group_value = str(row['Group'])
            digits = ''.join(char for char in group_value if char.isdigit())
            
            if digits:
                # Apply rules based on number of digits
                if len(digits) == 2:  # Double-digit number
                    df.at[index, 'Divison'] = digits[0]  # First digit only
                elif len(digits) > 2:  # More than 2 digits
                    df.at[index, 'Divison'] = digits[:2]  # First 2 digits
        
        # Determine output file path if not provided
        if output_path is None:
            base, ext = os.path.splitext(file_path)
            output_path = f"{base}_processed{ext}"
        
        # Save the updated Excel file
        df.to_excel(output_path, index=False)
        print(f"File processed successfully. Saved as: {output_path}")
        return df
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    # Specify your Excel file path here
    file_path = "C:\\Users\\saswa\\Downloads\\Test_NIC_Codes_cleaned.xlsx"
    process_division_groups(file_path)
