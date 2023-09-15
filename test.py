
filename = 'transcript.txt'

lines = []
with open(filename, 'r') as file:
    lines = file.readlines()

lines = [line[:-2] for line in lines]
text = ''.join(lines)
with open(filename, 'w') as file:
    file.write(text)

test = 'dfhsjfh'
print(''.join(test))