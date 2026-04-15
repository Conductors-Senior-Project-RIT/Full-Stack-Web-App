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
    
    return compare_results_ordered(e["results"], r["results"])
    
    
def compare_results_ordered(a: list[dict], b: list[dict]) -> tuple[bool, str | None]:
    """Compares the fields and values of the dictionaries in list 'a' with those in list 'b'.
    Fields present in list 'a' must be in 'b', but not vice versa. The order of the dictionaries must
    be the exact same between both lists.

    Args:
        a (list[dict]): List of dictionaries to compare from.
        b (list[dict]): List of dictionaries to compare with.

    Returns:
        tuple[bool, str | None]: A boolean that specifies whether the dictionaries match, and a string
        that specifies which fields do not match if present.
    """
    if len(a) != len(b):
        return False, "Number of instances do not match!"
    
    # Compare the fields and values of 'a' with those in 'b' 
    for i, instance in enumerate(a):
        for field in instance.keys():
            a_val = instance[field]
            
            if field not in b[i]:
                return False, f"Instance {i} in list B does not contain {field}."
            
            b_val = b[i][field]
            
            if b_val != a_val:
                return False, f"B's {field}: {b_val} != A's {field}: {a_val}"
    
    return True, None        
    

def compare_results_pkey(a: list[dict], b: list[dict], pk: str) -> tuple[bool, str | None]:
    if len(a) != len(b):
        return False, "Number of instances do not match!"
    
    # Check for duplicate primary keys in B
    b_pkeys = set()
    for i, instance_b in enumerate(b):
        if pk not in instance_b:
            return False, f"Instance {i} in list B does not contain {pk}."
        
        if instance_b[pk] in b_pkeys:
            return False, f"Duplicate {pk} in list B detected: {instance_b[pk]}."
        
        b_pkeys.add(instance_b[pk])
    
    # Check for duplicates in A
    a_pkeys = set()
    for i, instance_a in enumerate(a):
        if pk not in instance_a:
            return False, f"Instance {i} in list A does not contain {pk}."
        
        if instance_a[pk] in a_pkeys:
            return False, f"Duplicate {pk} in list A detected: {instance_a[pk]}."
        
        a_pkeys.add(instance_a[pk])

    # See if the pkeys in both A and B match up
    if a_pkeys != b_pkeys:
        only_in_a = a_pkeys - b_pkeys
        only_in_b = b_pkeys - a_pkeys
        return False, f"Primary key sets do not match! Only in A: {only_in_a}. Only in B: {only_in_b}."

    # Check to ensure that the fields and values from A match B
    for i, instance_a in enumerate(a):        
        # Find instance in B that has the same primary key
        instances = list(filter(lambda x: x[pk] == instance_a[pk], b))
        instance_b = instances[0]
        
        for field in instance_a.keys():
            # We already checked to see if pkeys match
            if field == pk:
                continue
            
            a_val = instance_a[field]
            
            if field not in instance_b:
                return False, f"Instance {i} in list B does not contain {field}."
            
            b_val = instance_b[field]
            
            if b_val != a_val:
                return False, f"B's {field}: {b_val} != A's {field}: {a_val}"
    
    return True, None