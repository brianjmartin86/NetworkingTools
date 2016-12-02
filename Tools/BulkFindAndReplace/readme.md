# HOW TO USE THIS SCRIPT

### This Script will read a file that you specify, and perform a find and replace all againste multipe strings all at once.
### First you must Edit the `replacements` dictionary at the beginning of the script to include all of the neccessary Find/Replace Strings to perform

### Example:
```
replacements = {
        'oldstring1': 'newstring1',
        'oldstring2': 'newstring2',
        'oldstring3': 'newstring3',
        'oldstring4': 'newstring4',
        'oldstring5': 'newstring5',
        'oldstring6': 'newstring6'
    }
```

## EXAMPLE USAGE:

* FORMAT: ./BulkFindAndReplace.py -f filename.txt

## OUTPUT EXAMPLE:

The conversion tool will parse through the config and output a new file with the string `_new` at the end

* FORMAT: filename_new.txt


Written By Brian Martin



