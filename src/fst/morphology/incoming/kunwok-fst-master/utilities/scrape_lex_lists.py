import json
import re

def main():

    bins = {}

    with open('resources/njamed_dictionary.json', "r") as json_file:
        data = json.load(json_file)

        for p in data:
            key = p['pos'].strip()
            key = re.sub('/', "_", key)
            if key in bins:
                bins[key].append(p['orth'])
            else:
                bins[key] = []
                bins[key].append(p['orth'])
    
    for k, v in bins.items():
        with open('resources/lexicons/' + k + ".txt", "w") as f:
            for item in v: 
                f.write(item + "\n")



if __name__ == "__main__":
    main()