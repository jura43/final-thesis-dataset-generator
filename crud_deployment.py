from kubernetes import client

def create_deployment(side, connect_to, number, port, node):
    """
    Params: - side (frontend, backend, database)
            - connect_to (frontend, backend)
            - number (int)
            - port (int)
            - node (str)
    """
    container = client.V1Container(
        name="final-thesis-"+side+"-"+str(number),
        image="docker.io/jura43/final-thesis-"+side,
        ports=[client.V1ContainerPort(container_port=port)],
        env=[client.V1EnvVar(name="hostname", value="final-thesis-"+connect_to+"-"+str(number))]
    )
    
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "final-thesis-"+side+"-"+str(number), "side": side, "number": str(number)}),
        spec=client.V1PodSpec(containers=[container], node_name=node)
    )

    spec = client.V1DeploymentSpec(
        replicas=1,
        template=template,
        selector={"matchLabels": {"app": "final-thesis-"+side+"-"+str(number)}}
    )

    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name="final-thesis-"+side+"-"+str(number), labels={"number": str(number), "side": side}),
        spec=spec
    )

    return deployment


def create_clusterIP(side, number, port):
    """
    Params: - side (frontend, backend, database)
            - number (int)
            - port (int)
    """
    spec=client.V1ServiceSpec(
        ports=[client.V1ServicePort(port=port, target_port=port, protocol="TCP")],
        selector={"app": "final-thesis-"+side+"-"+str(number)},
        type="ClusterIP"
    )
    metadata=client.V1ObjectMeta(name="final-thesis-"+side+"-"+str(number), labels={"number": str(number), "side": side})
    service=client.V1Service(api_version="v1", kind="Service", metadata=metadata, spec=spec)

    return service


def create_NodePort(number, port):
    """
    Params: - number (int)
            - port (int)
    """
    spec=client.V1ServiceSpec(
        ports=[client.V1ServicePort(port=port, target_port=port, node_port=30000+number, protocol="TCP")],
        selector={"app": "final-thesis-frontend-"+str(number)},
        type="NodePort"
    )
    metadata=client.V1ObjectMeta(name="final-thesis-frontend-"+str(number), labels={"number": str(number), "side": "frontend"})
    service=client.V1Service(api_version="v1", kind="Service", metadata=metadata, spec=spec)

    return service