"""Create test Excel file with complex structure."""

import numpy as np
import pandas as pd

# Create test data with empty rows at beginning
data = {
    'Company': ['', '', 'Apple', 'Google', 'Microsoft', 'Amazon', 'Tesla', ''],
    'Revenue (Billion $)': [np.nan, np.nan, 365.8, 257.6, 168.1, 469.8, 96.8, np.nan],
    'Industry': ['', '', 'Technology', 'Technology', 'Technology', 'E-commerce', 'Automotive', ''],
    'Founded': ['Header Info', 'Data Below', 1976, 1998, 1975, 1994, 2003, ''],
    'Employees': ['', '', 154000, 139995, 221000, 1608000, 127855, ''],
    'Description': ['', '',
                   'Leading technology company known for iPhone, Mac, and innovative consumer electronics',
                   'Search engine giant and technology conglomerate with diverse portfolio including Android and Cloud services',
                   'Software corporation famous for Windows OS, Office suite, and cloud computing platform Azure',
                   'E-commerce and cloud computing leader with extensive logistics and AWS infrastructure',
                   'Electric vehicle and clean energy company revolutionizing automotive and energy industries',
                   '']
}

df = pd.DataFrame(data)

# Create Excel file with multiple sheets
with pd.ExcelWriter('/Users/lihongwen/Documents/augment-projects/FastAI/test_documents/test_companies.xlsx', engine='openpyxl') as writer:
    # Main sheet with data
    df.to_excel(writer, sheet_name='Companies', index=False)

    # Summary sheet
    summary_data = {
        'Metric': ['Total Companies', 'Average Revenue', 'Top Industry', 'Oldest Company'],
        'Value': [5, 251.62, 'Technology', 'Microsoft (1975)']
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

    # Empty sheet
    empty_df = pd.DataFrame()
    empty_df.to_excel(writer, sheet_name='Empty', index=False)

print("Excel test file created successfully!")
