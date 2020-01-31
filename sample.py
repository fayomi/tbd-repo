import boto3
import json


lambda_client = boto3.client('lambda')

payload2 = {'Test': 'Account'}



# Test lambda invocation

response = lambda_client.invoke(
    FunctionName='test',
    # InvocationType='Event'|'RequestResponse'|'DryRun',
    # LogType='None'|'Tail',
    # ClientContext='string',
    Payload=json.dumps(payload2)
    # Qualifier='string'
)
payload = response['Payload'].read().decode("utf-8")
payload_json = json.loads(payload)
print(payload_json["body"])