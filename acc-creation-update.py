import os
from subprocess import Popen, PIPE
import boto3
import yaml
import json

ssm = boto3.client('ssm')
cloudformation = boto3.client('cloudformation')
lambda_client = boto3.client('lambda')
function_name = "account-creation-test"

create_stack_template_url = "https://dwp-test-create-account.s3-eu-west-1.amazonaws.com/simple-cf.yaml" #to be changed in test account
module_name = "create-account"
account_creation_lambda_s3_bucket_name = "dwp-test-lambda-account-creation" #to be changed in test account
account_creation_lambda_s3_bucket_key = "create-account.zip" #to be changed in test account

directory = os.listdir('./accounts')

# IF ACCOUNT IS NEW 
# Get the new account config.yaml and send the account name, ou name and email to stackset 
    # This scans to get all the data from the repo and saves it in a dictionary
file_dictionary = {}
for file_name in directory:
    file_path = "accounts/" + file_name
    process = Popen(['shasum', '-a', '256', file_path], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    stdout_formatter = stdout.split()
    file_hash = stdout_formatter[0].decode("utf-8")
    file_path = "/" + file_path
    file_dictionary[file_path] = file_hash

print("All Accounts in Repo:")
print(file_dictionary)

    # This scans to see if there is keys in the dictionary that are not in parameter 
path = "/accounts/"
created_accounts = {}
response = ssm.get_parameters_by_path(Path=path)
for item in response["Parameters"]:
    name = item["Name"]
    value = item["Value"]
    created_accounts[name] = value

print("created accounts:")
print(created_accounts)

#    This checks that all accounts in the repo exist in parameter store
difference = file_dictionary.keys() - created_accounts.keys()
print(difference)

# if the key does not exist then this means that a new account needs to be created
if len(difference) > 0:
    print("New Account to be created: " + str(difference))
    # Read configs from new account to be passed on as variables to account creation stackset
    
    creation_file_path = str(difference)
    creation_file_path = creation_file_path.split(", ")
    new_account_path = creation_file_path[0][2:-2:]
    # value = creation_file_path[1] [1:-3:]
    new_account_name = new_account_path[10:]

    # And return email, account name and ou name
    with open(r'.' + new_account_path) as file:
        config_list = yaml.load(file, Loader=yaml.FullLoader)
        account_name = config_list['name']
        account_email = config_list['email']
        ou_name = config_list['name']
        # stack_name = "create-account-" + account_name

        payload = {
            "account_name" : account_name,
            "account_email" : account_email,
            "ou_name" : ou_name
        }

        # Create new account

        response = lambda_client.invoke(
            FunctionName=function_name,
            # InvocationType='Event'|'RequestResponse'|'DryRun',
            # LogType='None'|'Tail',
            # ClientContext='string',
            Payload=json.dumps(payload)
            # Qualifier='string'
        )
        payload = response['Payload'].read().decode("utf-8")
        payload_json = json.loads(payload)
        print(payload_json)











        # response = cloudformation.create_stack(
        #     StackName=stack_name,
        #     # TemplateBody='string',
        #     TemplateURL=create_stack_template_url,
        #     Parameters=[
        #         {
        #             'ParameterKey': 'AccountName',
        #             'ParameterValue': account_name,
        #             'UsePreviousValue': False,
        #             # 'ResolvedValue': 'string'
        #         },
        #         {
        #             'ParameterKey': 'Email',
        #             'ParameterValue': account_email,
        #             'UsePreviousValue': False,
        #             # 'ResolvedValue': 'string'
        #         },
        #         {
        #             'ParameterKey': 'ModuleName',
        #             'ParameterValue': module_name,
        #             'UsePreviousValue': False,
        #             # 'ResolvedValue': 'string'
        #         },
        #         {
        #             'ParameterKey': 'OUName',
        #             'ParameterValue': ou_name,
        #             'UsePreviousValue': False,
        #             # 'ResolvedValue': 'string'
        #         },
        #         {
        #             'ParameterKey': 'S3Bucket',
        #             'ParameterValue': account_creation_lambda_s3_bucket_name,
        #             'UsePreviousValue': False,
        #             # 'ResolvedValue': 'string'
        #         },
        #         {
        #             'ParameterKey': 'S3Key',
        #             'ParameterValue': account_creation_lambda_s3_bucket_key,
        #             'UsePreviousValue': False,
        #             # 'ResolvedValue': 'string'
        #         },
        #     ],
        #     # DisableRollback=True|False,
        #     # RollbackConfiguration={
        #     #     'RollbackTriggers': [
        #     #         {
        #     #             'Arn': 'string',
        #     #             'Type': 'string'
        #     #         },
        #     #     ],
        #     #     'MonitoringTimeInMinutes': 123
        #     # },
        #     # TimeoutInMinutes=123,
        #     # NotificationARNs=[
        #     #     'string',
        #     # ],
        #     Capabilities=[
        #         'CAPABILITY_NAMED_IAM'
        #     ],
        #     # ResourceTypes=[
        #     #     'string',
        #     # ],
        #     # RoleARN='string',
        #     # OnFailure='DO_NOTHING'|'ROLLBACK'|'DELETE',
        #     # StackPolicyBody='string',
        #     # StackPolicyURL='string',
        #     # Tags=[
        #     #     {
        #     #         'Key': 'string',
        #     #         'Value': 'string'
        #     #     },
        #     # ],
        #     # ClientRequestToken='string',
        #     # EnableTerminationProtection=True|False
        # )

        # print(response)

    # ACCOUNT CREATION LAMBDA NEEDS TO HAVE THE STACKSET EXECUTION ROLE APPLIED TO IT







        # stack_id = response["StackId"]
        # stack_events = client.describe_stack_events(
        #     StackName=stack_id,
        #     # NextToken='string'
        # )
        # events = stack_events["StackEvents"]
        # for event in events:
        #     if event["LogicalResourceId"] == stack_name and event["ResourceStatus"] == "CREATE_COMPLETE":
        #         stack_output = cloudformation.describe_stacks(
        #             StackName=stack_name,
        #             # NextToken='string'
        #         )
        #         print(stack_output)
        #     else if event["ResourceStatus"] != "CREATE_COMPLETE" or event["ResourceStatus"] != "CREATE_IN_PROGRESS":





    # # hash the file
    # new_file_path = str(difference)
    # new_file_path = new_file_path[3:-2:]
    # print(new_file_path)
    # process = Popen(['shasum', '-a', '256', new_file_path], stdout=PIPE, stderr=PIPE)
    # stdout, stderr = process.communicate()
    # stdout_formatter = stdout.split()
    # file_hash = stdout_formatter[0].decode("utf-8")
    # file_path = "/" + new_file_path
    # # file_path = "/" + file_path
    # print("New hash:")
    # print(new_file_path + ": " + file_hash)
    # print("saving to parameter store")
    # # store the hashed file in parameter store
    # response = ssm.put_parameter(
    #     Name=file_path,
    #     Value=file_hash,
    #     Type='String'
    # )
    # print(response)
    # print("Account creation completed")

    # This creates an account and outputs account id
    # After the output is generated the next stackset is triggered, this configures the account based on things enabled in the yaml
    # Once this is complete the yaml file is hashed and the name and hash number are stored in parameter store
    # This parameter store is tagged with the account id and ou name


# IF ACCOUNT HAS BEEN UPDATED 
    # Get the account ID by searching the parameter store by  file name and searching the tags
    # Once account ID is retrieved the config yaml file is processed to extract the new data
    # The account provisioning stackset can be run to update the account with new configs
    # Once successfully updated the new file is hashed and the parameter store is updated with the new hash