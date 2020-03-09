"""Replace my name with User. Requires a file in this directory called dump.txt"""

def nameFilter():
    dump=[]
    with open("dump.txt", newline="") as f:
        for line in f:
            newLine=line.lower()
            newLine=newLine.replace("sam", "Username")
        
            dump.append(newLine)
    
    toStrip=["[", "]", "'"]
    output=f"{dump}"
    for char in toStrip:
        output=output.strip(char)


    
    import pyperclip
    pyperclip.copy(output)
    print(output)

    input("\nDump copied to clipboard. Press any key to exit")


if __name__ == "__main__":
    nameFilter()