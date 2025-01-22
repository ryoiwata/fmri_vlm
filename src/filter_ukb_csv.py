import csv
import sys
import argparse


def filter_csv_by_prefix(input_file: str, output_file: str, prefixes: list[str]) -> None:
    """
    Filters columns from a CSV file whose headers start with specific prefixes and writes them to a new CSV file.
    
    Parameters:
    ----------
    input_file: The path to the input CSV file.
    output_file: The path to the output CSV file where the filtered data will be saved.
    prefixes : A list of prefixes; columns whose headers start with any of these prefixes will be included.
    
    Returns:
    --------
    None
    """
    try:
        with open(input_file, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            matching_columns = [col for col in reader.fieldnames if any(col.startswith(prefix) for prefix in prefixes)]
            
            if not matching_columns:
                raise ValueError(f"No columns found starting with the provided prefixes: {prefixes}")
            
            with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=matching_columns, extrasaction='ignore')
                
                writer.writeheader()
                
                for row in reader:
                    filtered_row = {col: row[col] for col in matching_columns}
                    writer.writerow(filtered_row)
        
        print(f"Filtered CSV written to {output_file} with columns: {matching_columns}")
    
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except ValueError as ve:
        print(f"Error: {ve}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter specific columns from a CSV file.")
    parser.add_argument("input_file", help="Path to the input CSV file")
    parser.add_argument("output_file", help="Path to the output CSV file")
    parser.add_argument("codes", help="Comma-separated list of UKB codes to extract")
    
    args = parser.parse_args()

    prefixes = args.codes.split(",")
    
    filter_csv_by_prefix(args.input_file, args.output_file, prefixes)

