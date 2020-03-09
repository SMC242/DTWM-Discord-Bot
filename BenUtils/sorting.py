"""Various sorting algorithms."""

def bubbleSort(varList: list)-> list:
    '''Sorts a list of numbers ascending
    varList: a list of items to be sorted'''

    upper=len(varList)
    for i in range(0,upper):
        for index in range(0, (upper-1)):
            if varList[index]>varList[index+1]:
                varList[index+1], varList[index]=varList[index], varList[index+1]

    return varList


def insertionSort(arr: list) -> list:
    '''Sort the input list'''

    #check each element
    for outer in range(1, len(arr)):
        # store starting place
        current = arr[outer]
        i = outer
        
        # go down the list to prevent unnecessary comparisons
        while current < arr[i-1] and i > 0:
            arr[i] = arr[i - 1]
            i -= 1

        arr[i] = current  # the last checked index must be where current belongs

    return arr