import json
latency_data = 'json_data.json'
min_value = 100
permutation = '0-0-0'
with open(latency_data, 'r') as json_file:
    data = json.load(json_file)

    new_data = {}
    count = 0

    for permutation, workload_data in data.items():
        for workload, latency_data in workload_data.items():
            new_data[count] = {
                "permutation": permutation,
                "workload": float(workload)
            }
            count += 1

    # Convert the new data to JSON format
    new_json = json.dumps(new_data, indent=4)

    # Write the new JSON data to a file
    with open("new_data.json", "w") as outfile:
        outfile.write(new_json)
