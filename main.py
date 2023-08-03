import csv
import json
import grequests
import random
import time
from kubernetes import client
import crud_deployment as cd

token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ikw4Zl8zS3hzdmN5aVpXVi1lNkRzUVppUzZYLUxSMHI0RDNxdnhRRUgtcGsifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4iLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjRlN2I1YmExLTdhMjgtNGVhMC1iODVhLWI3ZWY5ODE3YTY5OSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.j980WjWTiosCv-4pjZDSnHwzCadDCpYn5FCRTIO90yJrRqBha5RMpST9NX2N08yjaIYARZwbd7WrvRD0hFfijFtBINTIwXyEXLg4pizVtBmWSvNz44saeZ62_Zql7L6Y1S6OzEqhqMj7YIfs5pGnEDbjrS5vw1qyKIdbB7XFF2YEpe2pFGQe9wWvsg1FxJUG-F6vK4NmXlrdatjhY1d3E_qpUn1YahUgPL8swTMqYwU-ETK1DL7wKUQcJjOoB30G9FSeNFML4JQ3ty4C5t7pxrzq8FJL37xD-mwy6v79Rr1XDVTHgHPMEB7ZeGmjRSI5zGBhO8VN_VXgoa3ebgT2ZQ"
with open('ssd.json') as f:
    ssd = json.load(f)

configuration = client.Configuration()
configuration.host = "http://192.168.21.130"
configuration.verify_ssl = False
#configuration.api_key = {"Authorization": "Bearer " + token}

ApiClient = client.ApiClient(configuration)

v1apps = client.AppsV1Api(ApiClient)
v1core = client.CoreV1Api(ApiClient)
api_custom = client.CustomObjectsApi(ApiClient)

# Number of replicas to create
instances = 3
# IP address of proxy to fetching created web site
ip = '192.168.21.130'
# Time in seconds to wait after creating deployment
wait = 25

# 0. Get list of all worker nodes
nodes = []
for n in v1core.list_node(label_selector="node=worker").items:
    if n.spec.unschedulable == None:
        for status in n.status.conditions:
            if status.status == "True" and status.type == "Ready":
                nodes.append(n.metadata.name)       

print("Nodes:")
print(nodes)

while True:
    # 1. Create deployment
    print("Creating "+ str(instances) + " deployments...")
    try:
        for i in range(instances):
            deployment_frontend = cd.create_deployment("frontend", "backend", i, 3000, node=nodes[random.randint(0, len(nodes)-1)])
            deployment_backend = cd.create_deployment("backend", "database", i, 5000, node=nodes[random.randint(0, len(nodes)-1)])
            deployment_database = cd.create_deployment("database", "none", i, 3306, node=nodes[random.randint(0, len(nodes)-1)])
            service_frontend = cd.create_NodePort(i, 3000)
            service_backend = cd.create_clusterIP("backend", i, 5000)
            service_database = cd.create_clusterIP("database", i, 3306)

            v1apps.create_namespaced_deployment(body=deployment_frontend, namespace="default")
            v1apps.create_namespaced_deployment(body=deployment_backend, namespace="default")
            v1apps.create_namespaced_deployment(body=deployment_database, namespace="default")
            v1core.create_namespaced_service(body=service_frontend, namespace="default")
            v1core.create_namespaced_service(body=service_backend, namespace="default")
            v1core.create_namespaced_service(body=service_database, namespace="default")
            
        print("Done")
        time.sleep(wait)
    except:
        print("Unable to create deployments, skipping...")
        for i in range(0, instances):
            v1apps.delete_namespaced_deployment(name="final-thesis-frontend-"+str(i), namespace="default")
            v1apps.delete_namespaced_deployment(name="final-thesis-backend-"+str(i), namespace="default")
            v1apps.delete_namespaced_deployment(name="final-thesis-database-"+str(i), namespace="default")
            v1core.delete_namespaced_service(name="final-thesis-frontend-"+str(i), namespace="default")
            v1core.delete_namespaced_service(name="final-thesis-backend-"+str(i), namespace="default")
            v1core.delete_namespaced_service(name="final-thesis-database-"+str(i), namespace="default")
        time.sleep(10)
        break


    # 2. Get pods info
    pods = [] # [{0: {'backend': 'minikube-m03', 'database': 'minikube-m03', 'frontend': 'minikube-m02', 'response_time': 3.931251}}]
    ips = []
    ret = v1core.list_pod_for_all_namespaces(watch=False, label_selector="number")

    for i in range(0, instances):
        entry = {i: {}}
        for p in ret.items:
            if p.metadata.labels['number'] == str(i):
                entry[i][p.metadata.labels['side']] = p.spec.node_name
                if p.metadata.labels['side'] == 'frontend':
                    entry[i]['frontend_ssd'] = ssd[p.spec.node_name]
                if p.metadata.labels['side'] == 'backend':
                    entry[i]['backend_ssd'] = ssd[p.spec.node_name]
                if p.metadata.labels['side'] == 'database':
                    entry[i]['database_ssd'] = ssd[p.spec.node_name]
        
            ips.append(p.status.host_ip)
        pods.append(entry)
        
    # 3. Get nodes resource usage
    nodes_info = {} # Nodes allocatable CPU, Memory and number of Pods, MemoryPressure, DiskPressure

    for n in v1core.list_node(label_selector="node=worker").items:
        if n.spec.unschedulable == None:
            nodes_info[n.metadata.name] = [n.status.allocatable['cpu'], n.status.allocatable['memory'][:-1][:-1], n.status.allocatable['pods']]
                     

    resource = api_custom.list_cluster_custom_object(group="metrics.k8s.io",version="v1beta1", plural="nodes")
    for i in range(instances):
        for n in resource['items']:
            if n['metadata']['name'] == pods[i][i]['frontend']:
                cpu = (int(n['usage']['cpu'][:-1])/1000000)/(int(nodes_info[pods[i][i]['frontend']][0])*1000)
                mem = int(n['usage']['memory'][:-1][:-1])/int(nodes_info[pods[i][i]['frontend']][1])
                pods[i][i]['frontend_cpu_usage'] = round(cpu, 2)
                pods[i][i]['frontend_memory_usage'] = round(mem,2)

            if n['metadata']['name'] == pods[i][i]['backend']:
                cpu = (int(n['usage']['cpu'][:-1])/1000000)/(int(nodes_info[pods[i][i]['backend']][0])*1000)
                mem = int(n['usage']['memory'][:-1][:-1])/int(nodes_info[pods[i][i]['backend']][1])
                pods[i][i]['backend_cpu_usage'] = round(cpu, 2)
                pods[i][i]['backend_memory_usage'] = round(mem, 2)

            if n['metadata']['name'] == pods[i][i]['database']:
                cpu = (int(n['usage']['cpu'][:-1])/1000000)/(int(nodes_info[pods[i][i]['database']][0])*1000)
                mem = int(n['usage']['memory'][:-1][:-1])/int(nodes_info[pods[i][i]['database']][1])
                pods[i][i]['database_cpu_usage'] = round(cpu, 2)
                pods[i][i]['database_memory_usage'] = round(mem, 2)


    # 4. Measure response time
    print("Measuring response time...")

    urls = []
    for i in range(0, instances): # Creating list of URLs for fetching website
        urls.append(grequests.get('http://'+ip+":"+str(30000+i)+"/shop"))

    try:
        res = grequests.map(urls)
        for i in range(instances):
            if res[i].status_code == 200:
                pods[i][i]['response_time'] = res[i].elapsed.total_seconds()
            else:
                pods[i][i]['response_time'] = -1

        # 5. Write CSV
        print("Writing data to CSV file...")
        with open('data.csv', 'a') as csv_file:
            columns = ['frontend', 'backend', 'database', 'response_time', 'frontend_cpu_usage', 'frontend_memory_usage', 'frontend_memory_pressure', 'frontend_disk_pressure', 'frontend_ssd', 'backend_cpu_usage', 'backend_memory_usage', 'backend_memory_pressure', 'backend_disk_pressure', 'backend_ssd', 'database_cpu_usage', 'database_memory_usage', 'database_memory_pressure', 'database_disk_pressure', 'database_ssd']
            writer = csv.DictWriter(csv_file, fieldnames=columns)

            for i in range(instances):
                if pods[i][i]['response_time'] != -1:
                    writer.writerow(pods[i][i])
    
    except:
        print("Unable to mesure time")

    # 6. Delete deployment
    print("Deleting "+ str(instances) + " deployments...")
    for i in range(0, instances):
        v1apps.delete_namespaced_deployment(name="final-thesis-frontend-"+str(i), namespace="default")
        v1apps.delete_namespaced_deployment(name="final-thesis-backend-"+str(i), namespace="default")
        v1apps.delete_namespaced_deployment(name="final-thesis-database-"+str(i), namespace="default")
        v1core.delete_namespaced_service(name="final-thesis-frontend-"+str(i), namespace="default")
        v1core.delete_namespaced_service(name="final-thesis-backend-"+str(i), namespace="default")
        v1core.delete_namespaced_service(name="final-thesis-database-"+str(i), namespace="default")
        
    print("Done, press CTRL+C in next 5s to stop the script")
    time.sleep(10)
