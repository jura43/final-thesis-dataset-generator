from kubernetes import client, config

configuration = client.Configuration()
configuration.host = "http://192.168.21.130"
configuration.verify_ssl = False
#configuration.api_key = {"Authorization": "Bearer " + token}

ApiClient = client.ApiClient(configuration)

v1apps = client.AppsV1Api(ApiClient)
v1core = client.CoreV1Api(ApiClient)
api = client.CustomObjectsApi(ApiClient)

resource = api.list_cluster_custom_object(group="metrics.k8s.io",version="v1beta1", plural="nodes")
print(resource)

for stats in resource['items']:
    print("Node Name: %s\tCPU: %s\tMemory: %s" % (stats['metadata']['name'], stats['usage']['cpu'], stats['usage']['memory']))

ret = v1core.list_namespaced_pod("default", watch=False)
for i in ret.items:
    if i.metadata.labels['app'] == 'final-thesis-frontend':
        print(i.spec.node_name)