import re
fileName = "forwarding_table.txt"

def readFile(file):
    f = open(file, 'r')
    for line in f:
    	print line
    	tmp = re.split('[ \n]+', line)
        new_entry = (tmp[0], tmp[1], tmp[2], tmp[3])
        print new_entry        
readFile(fileName)