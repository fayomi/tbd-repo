import os
from subprocess import Popen, PIPE
import boto3
import yaml

client = boto3.client('ssm')

directory = os.listdir('./accounts')

# IF ACCOUNT IS NEW 
    # Get the new account config.yaml and send the account name, ou name and email to stackset 
    # This creates an account and outputs account id
    # After the output is generated the next stackset is triggered, this configures the account based on things enabled in the yaml
    # Once this is complete the yaml file is hashed and the name and hash number are stored in parameter store
    # This parameter store is tagged with the account id and ou name


# IF ACCOUNT HAS BEEN UPDATED 
    # Get the account ID by searching the parameter store by  file name and searching the tags
    # Once account ID is retrieved the config yaml file is processed to extract the new data
    # The account provisioning stackset can be run to update the account with new configs
    # Once successfully updated the new file is hashed and the parameter store is updated with the new hash


# This scans to get all the data from the repo
file_dictionary = {}

for file_name in directory:
    file_path = "accounts/" + file_name
    process = Popen(['shasum', '-a', '256', file_path], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    stdout_formatter = stdout.split()
    file_hash = stdout_formatter[0].decode("utf-8")
    file_path = "/" + file_path
    file_dictionary[file_path] = file_hash

print("New Repo")
print(file_dictionary)

# This scans to see if there is keys in the dictionary that are not in parameter 

path = "/accounts/"
created_accounts = {}
response = client.get_parameters_by_path(Path=path)
for item in response["Parameters"]:
    name = item["Name"]
    value = item["Value"]
    created_accounts[name] = value

print("created accounts")
print(created_accounts)

# This checks that all accounts in the repo exist in parameter store
difference = file_dictionary.keys() - created_accounts.keys()

# if the key does not exist then it creates new file and updates the parameter store
if len(difference) > 0:
    print("New Account to be created: " + str(difference))
    # Read configs from new account to be passed on as variables to account creation stackset
    
    # hash the file
    new_file_path = str(difference)
    new_file_path = new_file_path[3:-2:]
    print(new_file_path)
    process = Popen(['shasum', '-a', '256', new_file_path], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    stdout_formatter = stdout.split()
    file_hash = stdout_formatter[0].decode("utf-8")
    file_path = "/" + new_file_path
    # file_path = "/" + file_path
    print("New hash:")
    print(new_file_path + ": " + file_hash)
    print("saving to parameter store")
    # store the hashed file in parameter store
    response = client.put_parameter(
        Name=file_path,
        Value=file_hash,
        Type='String'
    )
    print(response)
    print("Account creation completed")

    # update config.yaml with account id and ou
    # push back to the master repo which should trigger the pipeline again this time to apply the stacksets

    
else:
    # if the key exists but the value is different then it updates
    # scan all key / value pairs in repo and in parameter store to ensure nothing has changed
    account_difference = file_dictionary.items() - created_accounts.items()
    if len(account_difference) > 0:
        print("Account to be updated: " + str(account_difference))
        new_file_path = str(account_difference)
        new_file_path = new_file_path.split(", ")
        print(new_file_path)
        account_path = new_file_path[0][3:-1:]
        value = new_file_path[1] [1:-3:]
        account_name = account_path[10:]
        print("Print: " + account_name)
        # Read configs from account to be passed on as variables to stackset to be updated
        with open(r'./accounts/' + account_name) as file:
            config_list = yaml.load(file, Loader=yaml.FullLoader)
            print(config_list)

        # update value in parameter store of key once update is successful
        response = client.put_parameter(
            Name=account_path,
            Value=value,
            Type='String',
            Overwrite=True
        )
        print(response)

        print("Account was successfully updated")

    else:
        print("Nothing was updated")



    # if a yaml config file is deleted from repo
    # check organizational status to see if account is 'Suspended'
    # then delete account from aparameter store
