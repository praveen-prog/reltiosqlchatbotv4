import requests
import base64
import os
import csv
import ast
import pandas as pd
import sqlite3
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables for credentials and endpoints
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
base_url = os.getenv("base_url")

# Reltio OAuth URL
auth_url = "https://auth.reltio.com/oauth/token"

# Encode client ID and client secret in Base64
credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Define headers for the OAuth request
auth_headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Payload for OAuth token request with 'client_credentials' grant type
auth_payload = {
    "grant_type": "client_credentials",
}

class APICallClass:
# Function to retrieve OAuth token
    def __init__(self):
        pass

    def get_oauth_token(self):
        try:
            response = requests.post(auth_url, headers=auth_headers, data=auth_payload)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print("Access token retrieved successfully.")
                return access_token
            else:
                print(f"Failed to retrieve access token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"An error occurred while retrieving the access token: {e}")
            return None

# Function to get data from Reltio using OAuth token and handle pagination
    def get_reltio_data(self,unique_end_point):
        access_token = self.get_oauth_token()
        if not access_token:
            print("Unable to retrieve data due to missing access token.")
            return

        # Set up headers with the Bearer token for the data request
        data_headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Construct the initial data endpoint URL
        data_endpoint = f"{base_url}/entities?filter=(equals(type,'{unique_end_point}'))&pageSize=10000"
        cursor = None
        all_records = []

        try:
            while True:
                if cursor:
                    paginated_endpoint = f"{data_endpoint}&cursor={cursor}"
                else:
                    paginated_endpoint = data_endpoint

                response = requests.get(paginated_endpoint, headers=data_headers)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Data retrieved successfully for endpoint: {unique_end_point}")

                    # Ensure data is a list
                    if isinstance(data, list):
                        all_records.extend(data)
                    else:
                        print("Unexpected data format.")
                        break

                    # Check if more pages are available
                    cursor = response.headers.get("Next-Page-Cursor")
                    if not cursor:
                        break  # Exit loop if no more pages

                else:
                    print(f"Failed to retrieve data for {unique_end_point}: {response.status_code} - {response.text}")
                    break

            # Write all records to a CSV file specific to the endpoint
            if all_records:
                filename = "outputjson.csv"
                with open(filename, mode="w", newline="") as file:
                    headers = all_records[0].keys() if all_records else []
                    writer = csv.DictWriter(file, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(all_records)
                    print(f"Data written to {filename} successfully.")
            else:
                print(f"No records found for endpoint: {unique_end_point}")

        except Exception as e:
            print(f"An error occurred while retrieving data for {unique_end_point}: {e}")

    def extract_attributes(self):
        try:
            with open('outputjson.csv', 'r') as infile, open('outputattributes.csv', 'w', newline='') as outfile:
                reader = csv.reader(infile)
                writer = csv.writer(outfile)

                # Assuming the column you want is the first one (index 0)
                column_index = 6

                for row in reader:
                    writer.writerow([row[column_index]])
                print("Attributes extracted to outputattributes.csv successfully.")       
        except Exception as e:
            print(f"An error occurred while retrieving data: {e}")          

    #Flatten data process          
    def flatten_data_process(self):
        try:

            # Read CSV with dictionaries as rows
            with open('outputattributes.csv', 'r') as file:
                csv_reader = csv.DictReader(file)
                data = [row for row in csv_reader]
            # Function to extract values from the 'attributes' dictionary
                def extract_values(attributes_dict):
                    extracted_data = {}
                    for key, attribute_list in attributes_dict.items():
                        if isinstance(attribute_list, list) and len(attribute_list) > 0:
                            # For nested attributes in Address, flatten the dictionary
                            if isinstance(attribute_list[0]['value'], dict):
                                for sub_key, sub_list in attribute_list[0]['value'].items():
                                    extracted_data[f"{key}_{sub_key}"] = sub_list[0]['value']
                            else:
                                # Extract the main attribute value
                                extracted_data[key] = attribute_list[0]['value']
                    return extracted_data

                # List to store all rows of extracted data
                all_extracted_data = []

                # Process each row in data
                for row in data:
                    # Convert the 'attributes' value string to a dictionary
                    attributes_dict = ast.literal_eval(row['attributes'])
                    # Extract values from the attributes dictionary
                    extracted_data = extract_values(attributes_dict)
                    # Append the extracted data to the list
                    all_extracted_data.append(extracted_data)

                # Get headers dynamically from the first row
                headers = all_extracted_data[0].keys() if all_extracted_data else []

                # Write all extracted data to CSV
                with open("outputflattened.csv", "w", newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(all_extracted_data)

                print("Data has been written to outputflattened.csv")

        except Exception as e:
            print(f"An error occurred while retrieving data: {e}")  

    #Insert into SQL DB
    def sql_db_insert(self,unique_end_point):
        try:
            # Environment variables for credentials and endpoints

            
            table_name = os.path.basename(unique_end_point)

            # Define the path to your CSV file
            csv_file_path = 'outputflattened.csv'

            # Connect to SQLite database (or create it if it doesn't exist)
            conn = sqlite3.connect('patients.db')
            cursor = conn.cursor()

            # Read the CSV file to get column names and rows
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                # Get column names dynamically from the CSV file
                columns = reader.fieldnames
                
                # Generate the CREATE TABLE SQL statement dynamically based on column names
                create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{col} TEXT' for col in columns])});"
                #print(create_table_query)
                cursor.execute(create_table_query)

                # Prepare the INSERT INTO SQL statement
                insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])});"

                # Insert each row into the SQLite table
                for row in reader:
                    # Convert row values to a tuple, which is required for `execute`
                    values = tuple(row[col] for col in columns)
                    cursor.execute(insert_query, values)

            # Commit the transaction and close the connection
            conn.commit()
            conn.close()

            print("Data has been inserted into the SQLite database successfully.")


        except Exception as e:
            print(f"An error occurred while retrieving data: {e}")   

    #Perform DB Copy Process        
    def db_copy_process(self):
        try:
            source_path = os.getcwd()
            destination_path = os.path.join(source_path,'src')
            print(f"Source path is {source_path}")
            print(f"Destination path is {destination_path}")
            source_file = os.path.join(source_path,'patients.db')
            destination_file  = os.path.join(destination_path,'patients.db')

            shutil.move(source_file, destination_file)
            print("DB Copy is completed")

        except Exception as e:
            print(f"An error occurred while retrieving data: {e}")  
    
    def file_cleansing(self):
        try:
            file_path = ['outputjson.csv','outputattributes.csv','outputflattened.csv']
            for fle in file_path:
                if os.path.exists(fle):
                    print(f"Deleting file {fle}")
                    os.remove(fle)
                    print(f"Deleted file {fle}")
                else:
                    print(f"File {fle} is not found ")    

        except Exception as e:
            print(f"An error occurred while retrieving data: {e}")      

                    

######################################################################################        

    def execute_workflow(self):
        try:
            # List of unique endpoints to process
            patient_data_endpoints = [
                "configuration/entityTypes/Patient",
                "configuration/entityTypes/HealthCareProvider",
                "configuration/entityTypes/PatientAdmissionHistory",
                "configuration/entityTypes/BedUtilization",
                "configuration/entityTypes/StaffUtilization"

            ]

            # Loop through each endpoint and call the data retrieval function
            for unique_end_point in patient_data_endpoints:
                print(f"Processing endpoint: {unique_end_point}")
                self.get_reltio_data(unique_end_point)
                self.extract_attributes()
                self.flatten_data_process()
                self.sql_db_insert(unique_end_point)
            print("Initiating DB copy")
            #self.db_copy_process()   
            print("File Cleansing Started")
            self.file_cleansing() 

        except Exception as e:
            print(f"An error occurred while executing the workflow: {e}")

# Execute the workflow
#obj = APICallClass()
#obj.execute_workflow()
#execute_workflow()
