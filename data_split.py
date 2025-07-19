#!/usr/bin/env python3

def split_agent_output():
    """Split the AI Chat Widget API Response file into manageable chunks"""
    
    input_file = "/Users/keshav/Downloads/AI Chat Widget API Response.txt"
    
    try:
        print(f"Reading file: {input_file}")
        
        # Read all lines from the file
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        print(f"Total lines in file: {total_lines}")
        
        # Create start.txt - First 50 lines
        with open('start.txt', 'w', encoding='utf-8') as f:
            f.writelines(lines[:50])
        print(f"Created start.txt with {min(50, total_lines)} lines")
        
        # Create end.txt - Last 50 lines  
        with open('end.txt', 'w', encoding='utf-8') as f:
            f.writelines(lines[-50:] if total_lines >= 50 else lines)
        print(f"Created end.txt with {min(50, total_lines)} lines")
        
        # Create middle.txt - Lines around the middle (adjust based on total)
        if total_lines > 400:
            # For large files, take lines 200-300
            middle_start = 200
            middle_end = 300
        elif total_lines > 200:
            # For medium files, take middle third
            middle_start = total_lines // 3
            middle_end = min(middle_start + 100, total_lines - 50)
        else:
            # For small files, take what's available
            middle_start = 50 if total_lines > 100 else total_lines // 2
            middle_end = min(middle_start + 50, total_lines - 10)
        
        middle_lines = lines[middle_start:middle_end]
        with open('middle.txt', 'w', encoding='utf-8') as f:
            f.writelines(middle_lines)
        print(f"Created middle.txt with {len(middle_lines)} lines (lines {middle_start}-{middle_end})")
        
        print("\n✅ Successfully created:")
        print("  - start.txt (beginning of response)")
        print("  - middle.txt (sample from middle)")  
        print("  - end.txt (end of response)")
        
        print(f"\nFile sizes:")
        import os
        for filename in ['start.txt', 'middle.txt', 'end.txt']:
            size = os.path.getsize(filename)
            print(f"  {filename}: {size:,} bytes")
            
    except FileNotFoundError:
        print(f"❌ Error: Could not find file at {input_file}")
        print("Please check the file path is correct.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    split_agent_output()
