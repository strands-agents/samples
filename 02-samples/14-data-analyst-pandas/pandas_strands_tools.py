import pandas as pd
from typing import Any, Dict, List, Optional
from strands import tool

# Global DataFrame that all tools will operate on
df_glob = pd.DataFrame()

# Tools that load data and set df_glob

@tool
def pd_read_csv(filepath_or_buffer, sep=',', delimiter=None, header='infer', names=None, 
                index_col=None, usecols=None, dtype=None) -> str:
    """
    Read a comma-separated values (csv) file into the global DataFrame.
    
    Args:
        filepath_or_buffer: str, path object or file-like object
        sep: str, default ','
        delimiter: str, optional
        header: int, Sequence of int, 'infer' or None, default 'infer'
        names: Sequence of Hashable, optional
        index_col: Hashable, Sequence of Hashable or False, optional
        usecols: Sequence of Hashable or Callable, optional
        dtype: dtype or dict of {Hashable : dtype}, optional
    
    Returns:
        Status message with DataFrame shape
    """
    global df_glob
    df_glob = pd.read_csv(filepath_or_buffer=filepath_or_buffer, sep=sep, delimiter=delimiter, 
                          header=header, names=names, index_col=index_col, usecols=usecols, 
                          dtype=dtype)
    return f"Loaded CSV into df_glob: {df_glob.shape[0]} rows × {df_glob.shape[1]} columns"

@tool
def pd_read_excel(io, sheet_name=0, header=0, names=None, index_col=None, usecols=None, 
                  dtype=None) -> str:
    """
    Read an Excel file into the global DataFrame.
    
    Args:
        io: str, bytes, ExcelFile, xlrd.Book, path object, or file-like object
        sheet_name: str, int, list, or None, default 0
        header: int, list of int, default 0
        names: array-like, default None
        index_col: int, str, list of int, default None
        usecols: str, list-like, or callable, default None
        dtype: Type name or dict of column -> type, default None
    
    Returns:
        Status message with DataFrame shape
    """
    global df_glob
    df_glob = pd.read_excel(io=io, sheet_name=sheet_name, header=header, names=names,
                            index_col=index_col, usecols=usecols, dtype=dtype)
    return f"Loaded Excel into df_glob: {df_glob.shape[0]} rows × {df_glob.shape[1]} columns"

@tool
def pd_get_shape() -> str:
    """Get the shape of the global DataFrame."""
    global df_glob
    return f"df_glob shape: {df_glob.shape[0]} rows × {df_glob.shape[1]} columns"

@tool
def pd_get_columns() -> str:
    """Get column names from the global DataFrame."""
    global df_glob
    return f"df_glob columns: {list(df_glob.columns)}"

@tool
def pd_head(n: int = 5) -> str:
    """
    Return the first n rows of the global DataFrame.
    
    Args:
        n: int, default 5 - number of rows to return
    
    Returns:
        String representation of first n rows
    """
    global df_glob
    return df_glob.head(n).to_string()

@tool
def pd_tail(n: int = 5) -> str:
    """
    Return the last n rows of the global DataFrame.
    
    Args:
        n: int, default 5 - number of rows to return
    
    Returns:
        String representation of last n rows
    """
    global df_glob
    return df_glob.tail(n).to_string()

@tool
def pd_describe() -> str:
    """Generate descriptive statistics of the global DataFrame."""
    global df_glob
    return df_glob.describe().to_string()

@tool
def pd_info() -> str:
    """Get information about the global DataFrame."""
    global df_glob
    import io
    buffer = io.StringIO()
    df_glob.info(buf=buffer)
    return buffer.getvalue()

@tool
def pd_filter_rows(column: str, operator: str, value: Any) -> str:
    """
    Filter the global DataFrame based on a condition (modifies df_glob in place).
    
    Args:
        column: str - column name to filter on
        operator: str - comparison operator ('>', '<', '>=', '<=', '==', '!=')
        value: value to compare against
    
    Returns:
        Status message with new shape
    """
    global df_glob
    
    if operator == '>':
        df_glob = df_glob[df_glob[column] > value]
    elif operator == '<':
        df_glob = df_glob[df_glob[column] < value]
    elif operator == '>=':
        df_glob = df_glob[df_glob[column] >= value]
    elif operator == '<=':
        df_glob = df_glob[df_glob[column] <= value]
    elif operator == '==':
        df_glob = df_glob[df_glob[column] == value]
    elif operator == '!=':
        df_glob = df_glob[df_glob[column] != value]
    else:
        return f"Error: Unsupported operator: {operator}"
    
    return f"Filtered df_glob: {df_glob.shape[0]} rows remaining"

@tool
def pd_sort_values(by: str, ascending: bool = True) -> str:
    """
    Sort the global DataFrame by column (modifies df_glob in place).
    
    Args:
        by: str - column name to sort by
        ascending: bool, default True
    
    Returns:
        Status message
    """
    global df_glob
    df_glob = df_glob.sort_values(by=by, ascending=ascending)
    return f"Sorted df_glob by '{by}' ({'ascending' if ascending else 'descending'})"

@tool
def pd_drop_duplicates(subset: Optional[str] = None) -> str:
    """
    Remove duplicate rows from the global DataFrame (modifies df_glob).
    
    Args:
        subset: column label or sequence of labels, optional
    
    Returns:
        Status message with new shape
    """
    global df_glob
    original_rows = df_glob.shape[0]
    df_glob = df_glob.drop_duplicates(subset=subset)
    removed = original_rows - df_glob.shape[0]
    return f"Removed {removed} duplicate rows. df_glob now has {df_glob.shape[0]} rows"

@tool
def pd_dropna(axis: int = 0, how: str = 'any') -> str:
    """
    Remove missing values from the global DataFrame (modifies df_glob).
    
    Args:
        axis: {0/'index', 1/'columns'}, default 0
        how: {'any', 'all'}, default 'any'
    
    Returns:
        Status message with new shape
    """
    global df_glob
    original_rows = df_glob.shape[0]
    df_glob = df_glob.dropna(axis=axis, how=how)
    removed = original_rows - df_glob.shape[0]
    return f"Removed {removed} rows with NA values. df_glob now has {df_glob.shape[0]} rows"

@tool
def pd_fillna(value: Any) -> str:
    """
    Fill NA/NaN values in the global DataFrame (modifies df_glob).
    
    Args:
        value: scalar, dict, Series, or DataFrame - value to fill
    
    Returns:
        Status message
    """
    global df_glob
    df_glob = df_glob.fillna(value=value)
    return f"Filled NA values in df_glob with {value}"

@tool
def pd_rename_columns(columns: Dict[str, str]) -> str:
    """
    Rename columns in the global DataFrame (modifies df_glob).
    
    Args:
        columns: dict - mapping of old names to new names
    
    Returns:
        Status message
    """
    global df_glob
    df_glob = df_glob.rename(columns=columns)
    return f"Renamed columns in df_glob. New columns: {list(df_glob.columns)}"

@tool
def pd_select_columns(columns: List[str]) -> str:
    """
    Select specific columns from the global DataFrame (modifies df_glob).
    
    Args:
        columns: list of str - column names to keep
    
    Returns:
        Status message
    """
    global df_glob
    df_glob = df_glob[columns]
    return f"Selected columns in df_glob: {list(df_glob.columns)}"

@tool
def pd_groupby_sum(by: str, value_column: str) -> str:
    """
    Group the global DataFrame by column and sum (modifies df_glob).
    
    Args:
        by: str - column to group by
        value_column: str - column to sum
    
    Returns:
        String representation of grouped data
    """
    global df_glob
    result = df_glob.groupby(by)[value_column].sum()
    return result.to_string()

@tool
def pd_groupby_mean(by: str, value_column: str) -> str:
    """
    Group the global DataFrame by column and calculate mean.
    
    Args:
        by: str - column to group by
        value_column: str - column to average
    
    Returns:
        String representation of grouped data
    """
    global df_glob
    result = df_glob.groupby(by)[value_column].mean()
    return result.to_string()

@tool
def pd_value_counts(column: str) -> str:
    """
    Get value counts for a column in the global DataFrame.
    
    Args:
        column: str - column name
    
    Returns:
        String representation of value counts
    """
    global df_glob
    return df_glob[column].value_counts().to_string()

@tool
def pd_column_sum(column: str) -> str:
    """
    Sum a numeric column in the global DataFrame.
    
    Args:
        column: str - column name
    
    Returns:
        Sum as string
    """
    global df_glob
    return f"{column} sum: {df_glob[column].sum()}"

@tool
def pd_column_mean(column: str) -> str:
    """
    Calculate mean of a numeric column in the global DataFrame.
    
    Args:
        column: str - column name
    
    Returns:
        Mean as string
    """
    global df_glob
    return f"{column} mean: {df_glob[column].mean():.2f}"

@tool
def pd_column_max(column: str) -> str:
    """
    Get maximum value in a column of the global DataFrame.
    
    Args:
        column: str - column name
    
    Returns:
        Max value as string
    """
    global df_glob
    return f"{column} max: {df_glob[column].max()}"

@tool
def pd_column_min(column: str) -> str:
    """
    Get minimum value in a column of the global DataFrame.
    
    Args:
        column: str - column name
    
    Returns:
        Min value as string
    """
    global df_glob
    return f"{column} min: {df_glob[column].min()}"

@tool
def pd_reset_index() -> str:
    """Reset the index of the global DataFrame (modifies df_glob)."""
    global df_glob
    df_glob = df_glob.reset_index(drop=True)
    return "Reset df_glob index"

@tool
def pd_create_empty() -> str:
    """Create an empty global DataFrame."""
    global df_glob
    df_glob = pd.DataFrame()
    return "Created empty df_glob"

# List of all tools
pandas_tools = [
    pd_read_csv,
    pd_read_excel,
    pd_get_shape,
    pd_get_columns,
    pd_head,
    pd_tail,
    pd_describe,
    pd_info,
    pd_filter_rows,
    pd_sort_values,
    pd_drop_duplicates,
    pd_dropna,
    pd_fillna,
    pd_rename_columns,
    pd_select_columns,
    pd_groupby_sum,
    pd_groupby_mean,
    pd_value_counts,
    pd_column_sum,
    pd_column_mean,
    pd_column_max,
    pd_column_min,
    pd_reset_index,
    pd_create_empty,
]