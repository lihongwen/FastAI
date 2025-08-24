"""CSV and Excel parser with intelligent table detection."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chardet
from io import StringIO

from .base_parser import BaseParser, ParsedDocument


class CSVParser(BaseParser):
    """Parser for CSV and Excel files with intelligent table detection."""
    
    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if file is CSV or Excel format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def parse(self, file_path: Path) -> List[ParsedDocument]:
        """Parse CSV/Excel file with intelligent table detection."""
        try:
            if file_path.suffix.lower() == '.csv':
                df = self._read_csv_with_detection(file_path)
                sheet_name = 'Sheet1'  # CSV files don't have sheet names
            else:
                df, sheet_name = self._read_excel_with_detection(file_path)
            
            if df is None or df.empty:
                return []
            
            # Get base metadata
            base_metadata = self.get_file_metadata(file_path)
            base_metadata.update({
                'sheet_name': sheet_name,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'parser_type': 'csv_excel'
            })
            
            # Generate document chunks using different strategies
            documents = []
            
            # Strategy 1: Row-wise chunking (default)
            row_docs = self._create_row_based_chunks(df, base_metadata)
            documents.extend(row_docs)
            
            # Strategy 2: Summary document with table overview
            summary_doc = self._create_summary_document(df, base_metadata)
            if summary_doc:
                documents.append(summary_doc)
            
            return documents
            
        except Exception as e:
            # Create error document
            base_metadata = self.get_file_metadata(file_path)
            base_metadata['error'] = str(e)
            
            return [ParsedDocument(
                content=f"Error parsing {file_path.name}: {str(e)}",
                metadata=base_metadata
            )]
    
    def _read_csv_with_detection(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read CSV with encoding detection and smart table detection."""
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        encoding_result = chardet.detect(raw_data)
        encoding = encoding_result['encoding'] or 'utf-8'
        
        # Try different separators and detect header row
        separators = [',', ';', '\t', '|']
        best_df = None
        best_score = 0
        
        for sep in separators:
            try:
                # Read first 10 rows to detect header
                sample_df = pd.read_csv(
                    file_path, 
                    encoding=encoding, 
                    sep=sep, 
                    nrows=10,
                    header=None
                )
                
                if sample_df.empty:
                    continue
                
                # Find the best header row (first row with meaningful data)
                header_row = self._detect_header_row(sample_df)
                
                if header_row is not None:
                    # Read full file with detected header
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        sep=sep,
                        header=header_row,
                        skip_blank_lines=True
                    )
                    
                    # Score this configuration
                    score = self._score_dataframe(df)
                    if score > best_score:
                        best_score = score
                        best_df = df
                        
            except Exception:
                continue
        
        return best_df
    
    def _read_excel_with_detection(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], str]:
        """Read Excel with smart sheet and header detection."""
        try:
            # Get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            best_df = None
            best_score = 0
            best_sheet = sheet_names[0]
            
            for sheet_name in sheet_names:
                try:
                    # Read first 10 rows to detect header
                    sample_df = pd.read_excel(
                        file_path,
                        sheet_name=sheet_name,
                        nrows=10,
                        header=None
                    )
                    
                    if sample_df.empty:
                        continue
                    
                    # Find header row
                    header_row = self._detect_header_row(sample_df)
                    
                    if header_row is not None:
                        # Read full sheet
                        df = pd.read_excel(
                            file_path,
                            sheet_name=sheet_name,
                            header=header_row
                        )
                        
                        # Remove completely empty rows
                        df = df.dropna(how='all')
                        
                        score = self._score_dataframe(df)
                        if score > best_score:
                            best_score = score
                            best_df = df
                            best_sheet = sheet_name
                            
                except Exception:
                    continue
            
            return best_df, best_sheet
            
        except Exception:
            return None, ""
    
    def _detect_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Detect the row that contains the header."""
        if df.empty:
            return None
        
        for idx in range(min(10, len(df))):
            row = df.iloc[idx]
            
            # Skip completely empty rows
            if row.isna().all():
                continue
            
            # Check if this row looks like a header
            non_null_count = row.count()
            total_cols = len(row)
            
            # Header should have reasonable number of non-null values
            if non_null_count >= total_cols * 0.5:
                # Check for header-like characteristics
                row_values = row.dropna().astype(str)
                
                # Headers typically have:
                # 1. Mostly string values
                # 2. Unique values
                # 3. Reasonable length strings
                string_like = sum(1 for val in row_values if not val.isdigit()) >= len(row_values) * 0.7
                unique_ratio = len(row_values.unique()) / len(row_values) if len(row_values) > 0 else 0
                reasonable_length = all(len(str(val)) < 50 for val in row_values)
                
                if string_like and unique_ratio > 0.8 and reasonable_length:
                    return idx
        
        # If no clear header found, use first non-empty row
        for idx in range(min(5, len(df))):
            if not df.iloc[idx].isna().all():
                return idx
        
        return 0
    
    def _score_dataframe(self, df: pd.DataFrame) -> float:
        """Score the quality of parsed dataframe."""
        if df.empty:
            return 0
        
        score = 0
        
        # More columns generally better
        score += len(df.columns) * 0.1
        
        # More rows with data
        score += len(df) * 0.01
        
        # Less NaN values better
        total_cells = len(df) * len(df.columns)
        nan_ratio = df.isna().sum().sum() / total_cells if total_cells > 0 else 1
        score += (1 - nan_ratio) * 10
        
        # Column names should not be mostly unnamed
        unnamed_cols = sum(1 for col in df.columns if str(col).startswith('Unnamed'))
        unnamed_ratio = unnamed_cols / len(df.columns) if len(df.columns) > 0 else 0
        score += (1 - unnamed_ratio) * 5
        
        return score
    
    def _create_row_based_chunks(self, df: pd.DataFrame, base_metadata: Dict[str, Any]) -> List[ParsedDocument]:
        """Create documents from table rows with context."""
        documents = []
        
        # Get column names for context
        column_names = list(df.columns)
        column_context = f"Table columns: {', '.join(str(col) for col in column_names)}"
        
        for idx, row in df.iterrows():
            # Skip completely empty rows
            if row.isna().all():
                continue
            
            # Create row content with column context
            row_data = []
            for col, value in row.items():
                if pd.notna(value):
                    row_data.append(f"{col}: {value}")
            
            if not row_data:
                continue
            
            content = f"{column_context}\nRow {idx + 1}: " + "; ".join(row_data)
            
            # Row-specific metadata
            metadata = base_metadata.copy()
            metadata.update({
                'chunk_type': 'table_row',
                'row_index': int(idx),
                'columns_with_data': len(row_data),
                'chunk_id': f"row_{idx}"
            })
            
            documents.append(ParsedDocument(content=content, metadata=metadata))
        
        return documents
    
    def _create_summary_document(self, df: pd.DataFrame, base_metadata: Dict[str, Any]) -> Optional[ParsedDocument]:
        """Create a summary document describing the table structure."""
        try:
            summary_parts = []
            
            # Basic info
            summary_parts.append(f"Table Summary: {len(df)} rows, {len(df.columns)} columns")
            
            # Column information
            column_info = []
            for col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    data_type = "numeric" if pd.api.types.is_numeric_dtype(col_data) else "text"
                    unique_count = len(col_data.unique())
                    column_info.append(f"{col} ({data_type}, {unique_count} unique values)")
            
            if column_info:
                summary_parts.append("Columns: " + "; ".join(column_info))
            
            # Sample data (first few rows)
            if len(df) > 0:
                sample_rows = []
                for idx in range(min(3, len(df))):
                    row = df.iloc[idx]
                    row_data = [f"{col}: {val}" for col, val in row.items() if pd.notna(val)]
                    if row_data:
                        sample_rows.append(f"Row {idx + 1}: " + "; ".join(row_data))
                
                if sample_rows:
                    summary_parts.append("Sample data: " + " | ".join(sample_rows))
            
            content = "\n".join(summary_parts)
            
            metadata = base_metadata.copy()
            metadata.update({
                'chunk_type': 'table_summary',
                'chunk_id': 'summary',
                'column_names': list(df.columns),
                'data_types': {col: str(df[col].dtype) for col in df.columns}
            })
            
            return ParsedDocument(content=content, metadata=metadata)
            
        except Exception:
            return None