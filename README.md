This script was used to create dataset for machine learning model. Model can be found [here](https://github.com/jura43/ml-scheduler-model "here").

## How it works?
This script will indefinitely:
1. Create depolyment
2. Get information about number of running pods
3. Get resource usage of all worker nodes
4. Measure response time
5. Write data to CSV file
6. Delete deployment

## Dataset columns
- Frontend node
- Backend node
- Database node
- Response time of web app
- Frontend node CPU usage
- Frontend node memory usage
- Number of running pods on frontend node
- Storage type of frontend node (Loaded from JSON file)
- Backend node CPU usage
- Backend node memory usage
- Number of running pods on backend node
- Storage type of backend node (Loaded from JSON file)
- Database node CPU usage
- Database node memory usage
- Number of running pods on database node
- Storage type of database node (Loaded from JSON file)

## How to run?
To run this script you need to have:
- Kubernetes cluster
- Kubernetes metrics server
- Python 3.11 (Tested)
- Python modules specified in requirements files