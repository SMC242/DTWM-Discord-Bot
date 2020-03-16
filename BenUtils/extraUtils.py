"""Miscellaneous tools."""

from typing import Any, Hashable, Iterable, Tuple

def fileLength(f: str)->int:
    '''Opens the file and returns the number of lines. File path must be passed in.'''
    index=0
    with open(f) as f:
        for index, l in enumerate(f):
            pass
    return index+1


def fillListFromFile(file: str, floatVal: bool, varList: list=[])-> list:
    '''Takes in a file path and fills the input array with the contents of the file.
    varList: the list to fill. It will create itself if no list is passed in
    file: the file object
    floatVal: boolean value to indicate whether the file contents are numbers'''

    try:
        with open(file) as f:
            for line in f:
                newLine=line.strip("\n")
                newLine=newLine.lower()
                if floatVal:
                    newLine=float(newLine)
                varList.append(newLine)

        return varList

    except:
        raise Exception(f"{file} not found")


def getKeyFromDict(key: Hashable, target: dict) -> Any:
    """
    Recursively search for the key in target and return its value.
    
    RAISES
    KeyError:
        key is not in the target or its child dictionaries.
    """

    # hash() used to avoid issues with duplicate keys
    for currentKey, currentValue in target.items():
        if key == currentKey:
            return currentValue  # value found

        try:
            return getKeyFromDict(key, currentValue)

        # suppress errors raised by child calls
        # attribute error comes from no .items() method
        # key error comes from the key not being found by a child call
        # type error comes from a .items() method returning an unexpected value
        except (AttributeError, KeyError, TypeError):
            pass

    raise KeyError("key not found in target")


def removeFromDict(original: dict, toRemove: Iterable)-> Tuple[dict, dict]:
    '''Removes the keys of toRemove from the original dictionary.
    Returns the edited dict.
    Pure function as it does not edit the original dict.

    original: the dict to be edited
    toRemove: list or tuple of keys to remove from original
    labelParams=kwargsDict'''

    editedDict={}
            
    for key, value in original.items():
        try:
            if key not in toRemove:
                editedDict[key]=value

        except KeyError:
            #debugging information to remove upon release
            print(f"Key ({key}) not in original")

    return editedDict