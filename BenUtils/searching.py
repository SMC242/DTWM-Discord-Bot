"""Various searching algorithms."""

from typing import Any, List, Callable, Union

def binarySearch(target: Any, to_search: List[Any], return_type: str = "found",
                 key: Callable = None) -> Any:
    """Quickly iterate through the list to find the target.
    Supports any iterable that allows indexing.

    ARGUMENTS
        target:
            The element to find in the list.
        to_search:
            The list to find target in.
        return_type:
            What to return if target is found.
            Possible values:
                found: True if found, False if not found.
                index: int if found, None if not found.
                item: the element that contains target if found,
                    else None
        key:
            The callable that takes in an element
            and returns the value to compare against target.
            Defaults to lambda ele: ele"""
    # verify return_type
    if return_type not in ("found", "index", "item"):
        raise ValueError("Invalid return_type. See the docstring")

    # default value for key
    if not key:
        key = lambda ele: ele

    #standard binary search algorithm
    lower=0
    upper=len(to_search) - 1
    found=False

    while lower<=upper and not found:
        mid=lower + (upper - lower)//2  # find midpoint
        current = key(to_search[mid])  # accessing a stored variable is faster than accessing a list index

        if current < target:  # search is right of midpoint -> create higher midpoint
            lower = mid + 1

        elif current > target:  # search is left of midpoint -> create lower midpoint
            upper=mid-1

        else:
            found=True

    # if not return bool, check the other types
    if return_type == "found":
        return found
    if found:
        if return_type == "index":
            return mid
        if return_type == "item":
            return to_search[mid]
    else:
        return None

def sortSearch(targetList: Union[list, tuple], target: Any, returnBool: bool):
    """Wrapper around insertionSort and binarySearch."""

    # sort the list first, then search
    sortedList = insertionSort(targetList)
    return binarySearch(target, returnBool, varList = sortedList)