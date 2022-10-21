#!/Library/Frameworks/Python.framework/Versions/3.10/bin/python3
# pip3 install kubernetes==18.20.0
# [参考]('https://github.com/kubernetes-client/python/tree/release-18.0/examples')
from ast import Delete
import datetime
from tkinter import N
import pytz
import yaml
from kubernetes import client, config,utils,dynamic
import pathlib

class App:
    def __init__(self,api,name,namespace,expose_port,version):
        self.api = api
        self.name = name
        self.namespace = namespace
        self.expose_port = expose_port
        self.version = version

    def create_deployment_object(self,image,replicas,*options,**volume):            # 创建deployment的内容
        object = '''
client.V1Container(   #定义容器内容
    name=self.name,                                                                                              
    image=image,                                                                                 
    ports=[client.V1ContainerPort(container_port=self.expose_port)],
    '''+options[0]+'''
)
'''
        container = eval(object)
        if volume:                                                                                                                     
            template = client.V1PodTemplateSpec(    # 模版                                                                
                metadata=client.V1ObjectMeta(labels={"app": self.name,"version": self.version,"sidecar.istio.io/inject": "true"}), 
                spec=client.V1PodSpec(containers=[container],volumes=[client.V1Volume(name=volume['volume_name'],nfs=client.V1NFSVolumeSource(server=volume['nfs_ip'],path=volume['nfs_path'],))])) 
        else:
            template = client.V1PodTemplateSpec(    # 模版                                                                
                metadata=client.V1ObjectMeta(labels={"app": self.name,"version": self.version,"sidecar.istio.io/inject": "true"}),                 
                spec=client.V1PodSpec(containers=[container]))                                                         
        spec = client.V1DeploymentSpec(        # 详情                                                  
	        replicas=replicas,                                                                                      
	        template=template,selector={
            "matchLabels":
            {"app": self.name}})                                                                                      
        self.deployment = client.V1Deployment(                                                            
	        api_version="apps/v1",                                                                       
	        kind="Deployment",                                                                                      
	        metadata=client.V1ObjectMeta(name=self.name+'-'+self.version),                                                                
	        spec=spec)                                                                                              
        return self.deployment     
                           # 返回一个deployment对象                                                 
    def create_deployment(self):                                                      
        resp = self.api.create_namespaced_deployment(                                                   
            body=self.deployment,                                                                                        
            namespace=self.namespace)
        print("\n[INFO] deployment `"+self.name+'-'+self.version+"` created.\n")                                                                                 
        print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
        print(
            "%s\t\t%s\t%s\t\t%s\n"
            % (
                resp.metadata.namespace,
                resp.metadata.name,
                resp.metadata.generation,
                resp.spec.template.spec.containers[0].image,
            )
        )             

    def update_deployment(self,image=None,replicas=None):    # 更新deployments 
        if image is not None:
            deployment.spec.template.spec.containers[1].image = image 
        if replicas is not None:
            deployment.spec.replicas = replicas                                                  
        resp = self.api.patch_namespaced_deployment(                                                    
            name=self.name+'-'+self.version,                                                                                               
            namespace=self.namespace,                                                                                    
            body=self.deployment)                                                                                        
        print("\n[INFO] deployment's container image updated.\n")
        print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
        print(
            "%s\t\t%s\t%s\t\t%s\n"
            % (
                resp.metadata.namespace,
                resp.metadata.name,
                resp.metadata.generation,
                resp.spec.template.spec.containers[0].image,
            ) 
        )

    def restart_deployment(self):                                
	    # update `spec.template.metadata` section                           
	    # to add `kubectl.kubernetes.io/restartedAt` annotation             
	    deployment.spec.template.metadata.annotations = {                   
	        "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow() 
	        .replace(tzinfo=pytz.UTC)                                       
	        .isoformat()                                                    
	    }                                                                   
	                                                                        
	    # patch the deployment                                              
	    resp = api.patch_namespaced_deployment(                             
	        name=self.name+'-'+self.version, namespace=self.namespace, body=self.deployment      
	    )                                                                   
	                                                                        
	    print("\n[INFO] deployment `"+self.name+"-"+self.version+"` restarted.\n")        
	    print("%s\t\t\t%s\t%s" % ("NAME", "REVISION", "RESTARTED-AT"))      
	    print(                                                              
	        "%s\t%s\t\t%s\n"                                                
	        % (                                                             
	            resp.metadata.name,                                         
	            resp.metadata.generation,                                   
	            resp.spec.template.metadata.annotations,                    
	        )                                                               
	    )                

    def delete_deployment(self):        # 删除某个deployments                                    
        resp=self.api.delete_namespaced_deployment(                                                   
            name=self.name+'-'+self.version,                                                                                              
            namespace=self.namespace,                                                                                    
            body=client.V1DeleteOptions(                                                                            
                propagation_policy='Foreground',                                                                    
                grace_period_seconds=5))
        print("\n[INFO] deployment `"+self.name+"-"+self.version+"` deleted.")  

    def create_service(self):
        core_v1_api = client.CoreV1Api()
        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=self.name
            ),
            spec=client.V1ServiceSpec(
                selector={"app": self.name},
                ports=[client.V1ServicePort(
                    port=self.expose_port,
                    target_port=self.expose_port
                )]
            )
        )
        # Creation of the Deployment in specified namespace
        # (Can replace "default" with a namespace you may have created)
        core_v1_api.create_namespaced_service(namespace=self.namespace, body=body)


    def create_ingress(self,networking_v1_beta1_api):
        body = client.NetworkingV1beta1Ingress(
	        api_version="networking.k8s.io/v1beta1",
	        kind="Ingress",
	        metadata=client.V1ObjectMeta(name=self.name, annotations={
	            "nginx.ingress.kubernetes.io/rewrite-target": "/","nginx.ingress.kubernetes.io/upstream-vhost": self.name+"."+self.namespace+".svc.cluster.local"

	        }),
	        spec=client.NetworkingV1beta1IngressSpec(
	            rules=[client.NetworkingV1beta1IngressRule(
	                host=self.name+".demo.cn",
	                http=client.NetworkingV1beta1HTTPIngressRuleValue(
	                    paths=[client.NetworkingV1beta1HTTPIngressPath(
	                        path="/",
	                        backend=client.NetworkingV1beta1IngressBackend(
	                            service_port=self.expose_port,
	                            service_name=self.name)
	
	                    )]
	                )
	            )
	            ]
	        )
	    )
	    # Creation of the Deployment in specified namespace
	    # (Can replace "default" with a namespace you may have created)
        networking_v1_beta1_api.create_namespaced_ingress(
	        namespace=self.namespace,
	        body=body
	    )


def create_destinationrule(gray=False):
    dest_yaml = '''
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule 
metadata:             
  labels:             
    app: name
    app.kubernetes.io/name: name         
  name: name          
  namespace: namespace
spec:                 
  host: name          
  subsets:            
  - labels:           
      version: version
    name: name            
'''
    dest_yaml = yaml.load(dest_yaml, Loader=yaml.FullLoader)
    dest_yaml["metadata"]["name"] = "nginx"
    dest_yaml["metadata"]["namespace"] = "default"
    dest_yaml["metadata"]["labels"]["app"] = "nginx"
    dest_yaml["metadata"]["labels"]["app.kubernetes.io/name"] = "nginx"
    dest_yaml["spec"]["host"] = "nginx"
    dest_yaml["spec"]["subsets"][0]["labels"]["version"] = "v1"
    dest_yaml["spec"]["subsets"][0]["name"] = "nginx-v1"
    if gray == True:
        dest_yaml.update({"spec":{"subsets":[{"labels":{"version":"v1"},"name":"nginx-v1"},{"labels":{"version":"v2"},"name":"nginx-v2"}]}})
    with open("dest.yml", "w") as f:
        yaml.dump(dest_yaml, f)   

def create_virtualservicerule(gray=False):
    virtualsvc_yaml = '''
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  labels:
    app: name
    app.kubernetes.io/name: name
  name: name
  namespace: namespace
spec:
  hosts:
  - name
  http: []
  tcp:
  - match:
    - port: 8080
    route:
    - destination:
        host: name
        port:
          number: 8080
        subset: name
      weight: 100
'''
    virtualsvc_yaml = yaml.load(virtualsvc_yaml, Loader=yaml.FullLoader)
    virtualsvc_yaml["metadata"]["name"] = "nginx"
    virtualsvc_yaml["metadata"]["namespace"] = "default"
    virtualsvc_yaml["metadata"]["labels"]["app"] = "nginx"
    virtualsvc_yaml["metadata"]["labels"]["app.kubernetes.io/name"] = "nginx"
    virtualsvc_yaml["spec"]["hosts"][0] = "nginx"
    virtualsvc_yaml["spec"]["tcp"][0]["match"][0]["port"] = 80
    virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["destination"]["host"] = "nginx"
    virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["destination"]["port"]["number"] = 80
    virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["destination"]["subset"] = "nginx-v1"
    virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["weight"] = 100
    if gray == "canary":
        del virtualsvc_yaml["spec"]["tcp"]
        virtualsvc_yaml.update({'spec': {'hosts': ['nginx'], 'http': [{'match': [{'headers': {'end-user': {'exact': 'jason'}}}], 'route': [{'destination': {'host': 'nginx', 'subset': 'nginx-v2'}}]}, {'route': [{'destination': {'host': 'nginx', 'subset': 'nginx-v1'}}]}]}})
    elif gray == "blue":
        virtualsvc_yaml.update({'spec': {'hosts': ['nginx'], 'http': [], 'tcp': [{'match': [{'port': 80}], 'route': [{'destination': {'host': 'nginx', 'port': {'number': 80}, 'subset': 'nginx-v1'}, 'weight': 80}, {'destination': {'host': 'name', 'port': {'number': 80}, 'subset': 'nginx-v2'}, 'weight': 20}]}]}})
    else:
        pass
    with open("virtualsvc.yml", "w") as f:
        yaml.dump(virtualsvc_yaml, f)   

# 自定义CRD提交方法
def apply_simple_item(dynamic_client: dynamic.DynamicClient, manifest: dict, verbose: bool=False):
    api_version = manifest.get("apiVersion")
    kind = manifest.get("kind")
    resource_name = manifest.get("metadata").get("name")
    namespace = manifest.get("metadata").get("namespace")
    crd_api = dynamic_client.resources.get(api_version=api_version, kind=kind)

    try:
        crd_api.get(namespace=namespace, name=resource_name)
        crd_api.patch(body=manifest, content_type="application/merge-patch+json")
        if verbose:
            print(f"{namespace}/{resource_name} patched")
    except dynamic.exceptions.NotFoundError:
        crd_api.create(body=manifest, namespace=namespace)
        if verbose:
            print(f"{namespace}/{resource_name} created")

def delete_simple_item(dynamic_client: dynamic.DynamicClient, manifest: dict, verbose: bool=False):
    api_version = "networking.istio.io/v1beta1"
    kind = "VirtualService"
    crd_api = dynamic_client.resources.get(api_version=api_version, kind=kind)
    namespace = "default"
    name = "nginx"
    crd_api.get(namespace=namespace, name=name)
    crd_api.delete(namespace=namespace, name=name)
    print(f"{namespace}/{name} delete")

        

def apply_simple_item_from_yaml(dynamic_client: dynamic.DynamicClient, filepath: pathlib.Path, verbose: bool=False):
    with open(filepath, 'r') as f:
        manifest = yaml.safe_load(f)
        apply_simple_item(dynamic_client=dynamic_client, manifest=manifest, verbose=verbose)

def delete_simple_item_from_yaml(dynamic_client: dynamic.DynamicClient, filepath: pathlib.Path, verbose: bool=False):
    with open(filepath, 'r') as f:
        manifest = yaml.safe_load(f)
        delete_simple_item(dynamic_client=dynamic_client, manifest=manifest, verbose=verbose)

def create_destination(k8s_client):
    yaml_file = 'dest.yml'
    apply_simple_item_from_yaml(k8s_client,yaml_file,verbose=True)

def create_virtualservice(k8s_client):
    yaml_file = 'virtualsvc.yml'
    apply_simple_item_from_yaml(k8s_client,yaml_file,verbose=True)

def delete_virtualservice(k8s_client):
    yaml_file = 'virtualsvc-d.yml'
    delete_simple_item_from_yaml(k8s_client,yaml_file,verbose=True)

config.load_kube_config()
#提交自定义CRD，比如istio等第三方API
dest_yaml = create_destinationrule(gray=True)
virtualsvc_yaml = create_virtualservicerule(gray="canary")
k8s_client = dynamic.DynamicClient(
    client.api_client.ApiClient()
)
create_destination(k8s_client)
delete_virtualservice(k8s_client)
create_virtualservice(k8s_client)

# k8s标准API提交
apps_v1 = client.AppsV1Api() 
networking_v1_beta1_api = client.NetworkingV1beta1Api()                                                                     
create_app = App(apps_v1,"nginx","default",80,"v2")
#自定义pod属性：resources=client.V1ResourceRequirements(requests={"cpu": "500m", "memory": "512Mi"},limits={"cpu": "1000m", "memory": "1024Mi"},),volume_mounts=[client.V1VolumeMount(mount_path="/var/log/nginx",name="log",)],liveness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3),readiness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3)
#create_app.create_deployment_object("harbor.cechealth.cn/tools/nginx:1.20.1",1,'resources=client.V1ResourceRequirements(requests={"cpu": "500m", "memory": "512Mi"},limits={"cpu": "1000m", "memory": "1024Mi"},),volume_mounts=[client.V1VolumeMount(mount_path="/var/log/nginx",name="log",)],liveness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3),readiness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3)',volume_name="log",nfs_ip="172.16.56.225",nfs_path="/nfs/storage-class/log",mount_path="/var/log/nginx")
#create_app.create_deployment()
#create_app.create_service()
create_app.create_ingress(networking_v1_beta1_api)


if __name__ == '__main__':
    main()               # 运行主程序