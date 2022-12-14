#!/Library/Frameworks/Python.framework/Versions/3.10/bin/python3
# pip3 install kubernetes==18.20.0
# [参考]('https://github.com/kubernetes-client/python/tree/release-18.0/examples')
import datetime
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
    '''+options[0]+'''  #options 为pod属性设置比如liveness,volumemount等
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


def create_destinationrule(name,namespace,*version,gray=False):
    '''
参数说明:version为可变参数提供服务version元祖，("v1","v2"),举例：("nginx","default","v1","v2",gray=True)
'''
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
    dest_yaml["metadata"]["name"] = name
    dest_yaml["metadata"]["namespace"] = namespace
    dest_yaml["metadata"]["labels"]["app"] = name
    dest_yaml["metadata"]["labels"]["app.kubernetes.io/name"] = name
    dest_yaml["spec"]["host"] = name
    dest_yaml["spec"]["subsets"][0]["labels"]["version"] = version[0]
    dest_yaml["spec"]["subsets"][0]["name"] = name+'-'+version[0]
    if gray == True:
        dest_yaml.update({"spec":{"host":name,"subsets":[{"labels":{"version":version[0]},"name":name+'-'+version[0]},{"labels":{"version":version[1]},"name":name+'-'+version[1]}]}})
    with open("dest.yml", "w") as f:
        yaml.dump(dest_yaml, f)   

def create_virtualservicerule(name,namespace,expose_port,gray=False,**rule):
    '''
参数说明：rule参数正常模式version=version 最终函数获取的变量值：{"version":"v1"}，举例：("nginx","default",80,version="v1")
canary模式下： name_version2={"header-key":"header-value"},old_version=name_version1  最终函数获取到的变量值：{"name_version2":{"header-key":"header-value"},"old_version":"name-version1":"},举例：("nginx","default",80,gray="canary",nginx_v2={"end-user":"jason"},old_version="nginx_v1")
blue模式下：name_version1=weight1,name_version2=weight2 最终函数获取到的变量值：{"name_version1":"weight1","name_version2":"weight2"}，举例：("nginx","default",80,nginx_v2=20,nginx_v1=80)
'''
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
    virtualsvc_yaml["metadata"]["name"] = name
    virtualsvc_yaml["metadata"]["namespace"] = namespace
    virtualsvc_yaml["metadata"]["labels"]["app"] = name
    virtualsvc_yaml["metadata"]["labels"]["app.kubernetes.io/name"] = name
    virtualsvc_yaml["spec"]["hosts"][0] = name
    if gray == True:
        virtualsvc_yaml["spec"]["tcp"][0]["match"][0]["port"] = expose_port
        virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["destination"]["host"] = name
        virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["destination"]["port"]["number"] = expose_port
        virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["destination"]["subset"] = name+'-'+rule['version']
        virtualsvc_yaml["spec"]["tcp"][0]["route"][0]["weight"] = 100
    if gray == "canary":
        del virtualsvc_yaml["spec"]["tcp"]
        header_key = list(rule[list(rule.keys())[0]].keys())[0]
        header_value = rule[list(rule.keys())[0]][header_key]
        virtualsvc_yaml.update({'spec': {'hosts': [name], 'http': [{'match': [{'headers': {header_key: {'exact': header_value}}}], 'route': [{'destination': {'host': name, 'subset': list(rule.keys())[0].replace('_','-')}}]}, {'route': [{'destination': {'host': name, 'subset': rule['old_version'].replace('_','-')}}]}]}})
    elif gray == "blue":
        virtualsvc_yaml.update({'spec': {'hosts': [name], 'http': [], 'tcp': [{'match': [{'port': expose_port}], 'route': [{'destination': {'host': name, 'port': {'number': expose_port}, 'subset': list(rule.keys())[0].replace('_','-')}, 'weight': rule[list(rule.keys())[0]]}, {'destination': {'host': name, 'port': {'number': expose_port}, 'subset': list(rule.keys())[1].replace('_','-')}, 'weight': rule[list(rule.keys())[1]]}]}]}})
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

def get_simple_item(name,namespace,dynamic_client: dynamic.DynamicClient, manifest: dict, verbose: bool=False):
    api_version = manifest.get("apiVersion")
    kind = manifest.get("kind")
    crd_api = dynamic_client.resources.get(api_version=api_version, kind=kind)
    try:
        crd_api.get(namespace=namespace, name=name)
        if verbose:
            return True
            print(f"{namespace}/{resource_name} is exist")
    except dynamic.exceptions.NotFoundError:
        return False
        print(f"{namespace}/{resource_name} no exist")


def delete_simple_item(name,namespace,dynamic_client: dynamic.DynamicClient, manifest: dict, verbose: bool=False):
    api_version = manifest.get("apiVersion")
    kind = manifest.get("kind")
    crd_api = dynamic_client.resources.get(api_version=api_version, kind=kind)
    crd_api.get(namespace=namespace, name=name)
    crd_api.delete(namespace=namespace, name=name)
    print(f"{namespace}/{name} delete")

        

def apply_simple_item_from_yaml(dynamic_client: dynamic.DynamicClient, filepath: pathlib.Path, verbose: bool=False):
    with open(filepath, 'r') as f:
        manifest = yaml.safe_load(f)
        apply_simple_item(dynamic_client=dynamic_client, manifest=manifest, verbose=verbose)

def get_simple_item_from_yaml(name,namespace,dynamic_client: dynamic.DynamicClient, filepath: pathlib.Path, verbose: bool=False):
    with open(filepath, 'r') as f:
        manifest = yaml.safe_load(f)
        get_simple_item(name,namespace,dynamic_client=dynamic_client, manifest=manifest, verbose=verbose)

def delete_simple_item_from_yaml(name,namespace,dynamic_client: dynamic.DynamicClient, filepath: pathlib.Path, verbose: bool=False):
    with open(filepath, 'r') as f:
        manifest = yaml.safe_load(f)
        delete_simple_item(name,namespace,dynamic_client=dynamic_client, manifest=manifest, verbose=verbose)

def create_destination(k8s_client):
    yaml_file = 'dest.yml'
    apply_simple_item_from_yaml(k8s_client,yaml_file,verbose=True)

def create_virtualservice(k8s_client):
    yaml_file = 'virtualsvc.yml'
    apply_simple_item_from_yaml(k8s_client,yaml_file,verbose=True)

def get_virtualservice(k8s_client,name,namespace):
    yaml_file = 'virtualsvc.yml'
    get_simple_item_from_yaml(name,namespace,k8s_client,yaml_file,verbose=True)

def delete_virtualservice(k8s_client,name,namespace):
    yaml_file = 'virtualsvc.yml'
    delete_simple_item_from_yaml(name,namespace,k8s_client,yaml_file,verbose=True)

config.load_kube_config()
#提交自定义CRD，比如istio等第三方API
dest_yaml = create_destinationrule("nginx","default","v1","v2",gray=True)
virtualsvc_yaml = create_virtualservicerule("nginx","default",80,gray="canary",nginx_v2={"end-user":"jason"},old_version="nginx_v1")
k8s_client = dynamic.DynamicClient(
    client.api_client.ApiClient()
)
create_destination(k8s_client)
if get_virtualservice(k8s_client,"nginx","default"):
    delete_virtualservice(k8s_client,"nginx","default")
create_virtualservice(k8s_client)

# k8s标准API提交
apps_v1 = client.AppsV1Api() 
networking_v1_beta1_api = client.NetworkingV1beta1Api()                                                                     
create_app = App(apps_v1,"nginx","default",80,"v2")
#自定义pod属性：resources=client.V1ResourceRequirements(requests={"cpu": "500m", "memory": "512Mi"},limits={"cpu": "1000m", "memory": "1024Mi"},),volume_mounts=[client.V1VolumeMount(mount_path="/var/log/nginx",name="log",)],liveness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3),readiness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3)
#create_app.create_deployment_object("harbor.cechealth.cn/tools/nginx:1.20.1",1,'resources=client.V1ResourceRequirements(requests={"cpu": "500m", "memory": "512Mi"},limits={"cpu": "1000m", "memory": "1024Mi"},),volume_mounts=[client.V1VolumeMount(mount_path="/var/log/nginx",name="log",)],liveness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3),readiness_probe=client.V1Probe(tcp_socket=client.V1TCPSocketAction(port=80),initial_delay_seconds=45,period_seconds=10,failure_threshold=3)',volume_name="log",nfs_ip="172.16.56.225",nfs_path="/nfs/storage-class/log",mount_path="/var/log/nginx")
#create_app.create_deployment()
#create_app.create_service()
#create_app.create_ingress(networking_v1_beta1_api)


if __name__ == '__main__':
    main()               # 运行主程序