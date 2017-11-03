#!/bin/env python

import pprint, sys, boto3, json
from datetime import datetime
from datetime import date
from argparse import ArgumentParser as parser
import ConfigParser as config



class MyException(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)

#priority = None
#message = None
    
def log(message="",priority=""):
    print "[%s] %s: %s" % (datetime.utcnow(),priority,message)

def create(client,stack_name,template_body,params):
    try:
        log("Create stack called","INFO")
        response = client.create_stack(
            StackName = stack_name,
            TemplateBody = template_body,
            Parameters=[params]
            #Capabilities=[capabilities],
            #OnFailure='ROLLBACK',
            #EnableTerminationProtection=True
        )
    except Exception as e:
        log(e,"Error")


def update(client,stack_name,template_body,params):
    try:
        log("Update stack called","INFO")
        response = client.update_stack(
            StackName = stack_name,
            TemplateBody = template_body,
            Parameters=[params]
            #TimeoutInMinutes=30,
            #Capabilities=[capabilities],
            #OnFailure='ROLLBACK',
            #EnableTerminationProtection=True
        )
    except Exception as e:
        log(e,"Error")        
        

arg = parser(description='Get additional arguments')
arg.add_argument("-op","--operation",help="operation", dest="operation", required=False)

args = arg.parse_args()
op = args.operation

config = config.ConfigParser()
config.optionxform=str

config.read("config.ini")

options = config.items("production-stack-params")

params = {}

for k,v in options:
    params["ParameterKey"] = k
    params["ParameterValue"] = v

client = boto3.client('cloudformation')


stack_name = config.get("common","stackname")
capabilities = config.get("common","capabilities")

vpc_resource = {
               "Type": "AWS::EC2::VPC",
               "Properties":{
                    "CidrBlock": {"Ref":"Cidr"}
                   }
    }

#ebs_volume = {
#   "Type":"AWS::EC2::Volume",
#   "Properties" : {
#      "AvailabilityZone" : "us-west-2b",
#      "Encrypted" : True,
#      "Size" : 30,
#      "Tags" : [ {"Key":"Name","Value":"Kube Monitoring"}],
#      "VolumeType" : "gp2"        
#    }
#   }
   
#volume_attachment = {
#   "Type":"AWS::EC2::VolumeAttachment",
#   "Properties" : {
#      "Device" : "/dev/xvda",
#      "InstanceId" : {"Ref":"KubeMonitorEc2Instance"},
#      "VolumeId" : {"Ref":"KubeMonitorVolume"}
#   }
#}
   
kube_monitor_sg = {
  "Type" : "AWS::EC2::SecurityGroup",
   "Properties" : {
      "GroupDescription" : "Allow http to client host",
      "VpcId" : {"Ref" : "nestedexamplevpc"},
      "SecurityGroupIngress" : [{
            "IpProtocol" : "tcp",
            "FromPort" : "22",
            "ToPort" : "22",
            "CidrIp" : "10.10.10.10/32"
         }]
   }
}
   
kube_monitor_subnet = {
        "Type" : "AWS::EC2::Subnet",
         "Properties" : {
            "VpcId" : { "Ref" : "nestedexamplevpc" },
            "CidrBlock" : "10.50.0.0/24",
            "AvailabilityZone" : "us-west-2b",
            "Tags" : [ { "Key" : "Name", "Value" : "Kube Monitor Subnet" } ]
         }
    }

ec2_instance = {
        "Type" : "AWS::EC2::Instance",
        "Properties" : {
              "ImageId":"ami-e689729e",
              "AvailabilityZone" : "us-west-2b",
              "BlockDeviceMappings" : [
                     {
                        "DeviceName" : "/dev/xvda",
                        "Ebs" : { "VolumeSize" : "30" }
                     }
                ],
              "DisableApiTermination" : False,
              "InstanceType" : "t2.micro",
              "KeyName" : "kube-dev-instance",
              
              "Tags" : [ {"Key":"Name","Value":"Kube Monitoring"}],
              "Tenancy" : "default",
              "NetworkInterfaces": [ {
                  "AssociatePublicIpAddress": "true",
                  "DeviceIndex": "0",
                  "GroupSet": [{ "Ref" : "KubeMonitorSG" }],
                  "SubnetId" : {"Ref":"KubeMonitorSubnet"}
      
                } ]
            }
    }

template_body = json.dumps({
        "Parameters":{
                "Cidr":{
                        "Type":"String",
                        "Description":"Testing instance tenancy.",
                        "Default":"10.0.0.0/16"
                    }
            },
        "Resources":{
                     "%s" % config.get("vpc","name"): vpc_resource,
                     "KubeMonitorSG" : kube_monitor_sg,
                     "KubeMonitorSubnet": kube_monitor_subnet,
                     #"KubeMonitorVolume":ebs_volume,
                     #"KubeMonitorAttachment": volume_attachment,
                     "KubeMonitorEc2Instance": ec2_instance
                 }
    })

response = None

try:

    if op == 'create':
        response = create(client,stack_name,template_body,params)
        print response
    elif op == 'update':
        response = update(client,stack_name,template_body,params)
        print response
    elif op == 'delete':
        pass
        #delete()
    else:
        response = create(client,stack_name,template_body,params)
        print response

    log(response,"INFO")
    log("HTTP Status Code %s" % response['HTTPStatusCode'],"INFO")

except:
    log("Error","ERROR")




