# Klassenlabels aus imagenet1000_clsidx_to_labels.txt auslesen

classes = {}

with open("imagenet1000_clsidx_to_labels.txt", 'r') as f:
    for line in f:
       line = line.rstrip()
       #print(f'[DEBUG]: line)
       key, val = line.split(':')
       #print(f'[DEBUG] {key} : {val}')
       classes[int(key)] = val

#print(f'[DEBUG]: {classes}')
print(f'[INFO]: Imagenet Labels geladen...')