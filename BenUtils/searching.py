"""Various searching algorithms."""

from typing import Union, Any

def binarySearch(search: str, returnBool: bool, file: str=None, varList: list=None)->Union[int, bool]:
    '''Binary searches the input file path or list for search.
    Outputs either the index or a boolean value.
    returnBool: 
    file: the string file path to be searched. Defaults to None
    varList: the list to be searched. Defaults to None'''

    #ensuring that a file or list is passed in
    fail=False

    isFile=file is None
    if isFile is True:
        fail=varList is None
        if fail:
            raise ValueError("No file or list passed into binarySearch")

    if not isFile:
        with open(file) as f:
            fileText=f.readlines()
            lines=[]
            for item in fileText:
                newItem=item.strip("\n")
                lines.append(newItem)

    else:
        lines=varList

    #standard binary search algorithm
    lower=0
    upper=len(lines)-1
    found=False

    while lower<=upper and not found:
        mid=(lower+upper)//2  # find midpoint
        current = lines[mid]  # accessing a stored variable is faster than accessing a list index

        if current==search:  # found
            found=True

        elif search< current:  # search is left of midpoint -> create lower midpoint
            upper=mid-1

        else:  # search is right of midpoint -> create higher midpoint
            lower=mid+1

    if returnBool:#returns boolean
        return found
    else:#returns index
        return mid


def sortSearch(targetList: Union[list, tuple], target: Any, returnBool: bool):
    """Wrapper around insertionSort and binarySearch."""

    sortedList = insertionSort(targetList)
    return binarySearch(target, returnBool, varList = sortedList)