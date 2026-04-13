def collation_valid(e: dict, r: dict) -> tuple[bool, str | None]:
    """
    The return value of a record collation is a dictionary containing two keys: 'results' and 'totalPages'.
    Results contains a list of dictionaries containing the resulting records from the collation query.
    Total pages contains the total number of pages of collation results from the size of a page given.

    Args:
        e (dict): The expected results of a collation operation.
        r (dict): The actual results of a collation operation.

    Returns:
        tuple[bool, str | None]: A tuple containing whether the expected and actual results match, and a message 
        specifying the mismatch if present.
    """
    if "results" not in r:
        return False, "'results' key does not exist."
    
    if "totalPages" not in r:
        return False, "'totalPages' does not exist."
    
    if r["totalPages"] != e["totalPages"]:
        return False, f"Actual Total Pages: {r["totalPages"]} != Expected Total Pages: {e["totalPages"]}"
    
    return compare_results(e["results"], r["results"])
    
    
def compare_results(e: list[dict], r: list[dict]) -> tuple[bool, str | None]:
    if len(e) != len(r):
        return False, "Number of results do not match!"
    
    try:
        # Compare the expected values with the actual values given
        for i, row in enumerate(e):
            for field in row.keys():
                expected_val = row[field]
                
                if field not in r[i]:
                    return False, f"Actual row {i} does not contain {field}."
                
                actual_val = r[i][field]
                
                if actual_val != expected_val:
                    return False, f"Actual {field}: {actual_val} != Expected {field}: {expected_val}"
        
        return True, None        
        
    except KeyError as e:
        return False, str(e)