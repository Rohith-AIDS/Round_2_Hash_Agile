#!/usr/bin/env python
# coding: utf-8

# In[1]:


pip install --upgrade elasticsearch


# In[2]:


import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import AuthenticationException


# In[3]:



# Connect to Elasticsearch
es = Elasticsearch(
    ['https://localhost:9200'],  # Ensure HTTPS is used
    http_auth=('elastic', 'X1OymygDczYaVS3YujHS'),  # Your credentials
    verify_certs=False  # Set to False if you're using a self-signed certificate
)

# Check if the connection is successful
if es.ping():
    print("Connected to Elasticsearch!")
else:
    print("Could not connect to Elasticsearch.")


# In[4]:


import pandas as pd
index_name = 'employee_data'

# Load Employee data using pandas with specified encoding
data = pd.read_csv('employee.csv', encoding='ISO-8859-1')

# Replace NaN values with None (or a default value)
data = data.where(pd.notnull(data), None)  # Replace NaN with None

# Now 'data' contains the loaded employee data with NaN replaced by None
print(data.head())  # Print the first few rows to verify the data


# In[20]:



def createCollection(p_collection_name):
    """
    Function to create an Elasticsearch index with the specified name.
    
    Parameters:
    p_collection_name (str): The name of the Elasticsearch index to create.

    Returns:
    bool: True if the index was created successfully, False otherwise.
    """
    try:
        # Define index settings and mappings (if needed)
        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "Employee ID": {"type": "keyword"},
                    "Full Name": {"type": "text"},
                    "Job Title": {"type": "text"},
                    "Department": {"type": "keyword"},
                    "Business Unit": {"type": "text"},
                    "Gender": {"type": "keyword"},
                    "Ethnicity": {"type": "keyword"},
                    "Age": {"type": "integer"},
                    "Hire Date": {"type": "date"},
                    "Annual Salary": {"type": "float"},
                    "Bonus %": {"type": "float"},
                    "Country": {"type": "keyword"},
                    "City": {"type": "text"},
                    "Exit Date": {"type": "date"}
                }
            }
        }

        # Create the index
        if not es.indices.exists(index=p_collection_name):
            es.indices.create(index=p_collection_name, body=index_body)
            print(f"Index '{p_collection_name}' created successfully!")
            return True
        else:
            print(f"Index '{p_collection_name}' already exists.")
            return False

    except Exception as e:
        print(f"An error occurred while creating the index: {e}")
        return False


# In[ ]:


def indexData(p_collection_name, p_exclude_column):
    """
    Function to index employee data into the specified collection, excluding the specified column.
    
    Parameters:
    p_collection_name (str): The name of the Elasticsearch index.
    p_exclude_column (str): The name of the column to exclude during indexing.

    Returns:
    None
    """
    try:
        # Load Employee data using pandas with specified encoding
        data = pd.read_csv('employee.csv', encoding='ISO-8859-1')

        # Replace NaN values with None
        data = data.where(pd.notnull(data), None)

        # Exclude the specified column
        if p_exclude_column in data.columns:
            data = data.drop(columns=[p_exclude_column])
            print(f"Excluding column: {p_exclude_column}")
        else:
            print(f"Column '{p_exclude_column}' not found in the data. All columns will be indexed.")

        # Index each record into Elasticsearch
        for i, record in data.iterrows():
            doc = record.to_dict()  # Convert each row to a dictionary
            try:
                # Index the document and capture the response
                response = es.index(index=p_collection_name, id=i, document=doc)  
                
                # Print the indexed document details
                print(f"Indexed document {i + 1}/{len(data)}:")
                print(f"Document ID: {response['_id']}, Version: {response['_version']}, Result: {response['result']}")
                print(f"Document Data: {doc}\n")
            except Exception as e:
                print(f"An error occurred while indexing document {i}: {e}")

        print("All documents indexed successfully!")

    except Exception as e:
        print(f"An error occurred while loading or processing the data: {e}")


# In[15]:


def getEmpCount(index_name):
    """
    Function to get the count of employee documents in the specified index.
    
    Parameters:
    index_name (str): The name of the Elasticsearch index.

    Returns:
    int: The count of documents in the index.
    """
    try:
        # Use the count API to get the number of documents
        count_response = es.count(index=index_name)
        count = count_response['count']
        print(f"Total number of employees indexed: {count}")
        return count
    except Exception as e:
        print(f"An error occurred while counting documents: {e}")
        return 0  # Return 0 if there's an error


# In[16]:


def searchByColumn(p_collection_name, p_column_name, p_column_value):
    """
    Function to search for records in the specified collection where the column matches the given value.
    
    Parameters:
    p_collection_name (str): The name of the Elasticsearch index.
    p_column_name (str): The name of the column to search.
    p_column_value (str): The value to match against the specified column.

    Returns:
    list: A list of matched records.
    """
    try:
        # Define the search query
        query = {
            "query": {
                "match": {
                    p_column_name: p_column_value
                }
            }
        }

        # Perform the search query
        response = es.search(index=p_collection_name, body=query)
        matches = response['hits']['hits']  # Get the matched documents

        # Print the results
        if matches:
            print(f"Found {len(matches)} record(s) matching '{p_column_name}': '{p_column_value}':")
            for match in matches:
                print(f"Document ID: {match['_id']}, Data: {match['_source']}")
        else:
            print(f"No records found matching '{p_column_name}': '{p_column_value}'")

        return [match['_source'] for match in matches]  # Return matched records

    except Exception as e:
        print(f"An error occurred during the search: {e}")
        return []  # Return an empty list if there's an error


# In[51]:


def checkAndDeleteEmployee(p_collection_name, p_employee_id):
    """
    Function to check if an employee record exists and delete it if it does.
    
    Parameters:
    p_collection_name (str): The name of the Elasticsearch index.
    p_employee_id (str): The ID of the employee to delete.

    Returns:
    bool: True if the deletion was successful, False otherwise.
    """
    try:
        # Check if the document exists
        es_response = es.exists(index=p_collection_name, id=p_employee_id)
        
        if es_response:
            # Attempt to delete the document
            response = es.delete(index=p_collection_name, id=p_employee_id)
            if response['result'] == 'deleted':
                print(f"Successfully deleted employee with ID: {p_employee_id}")
                return True
            else:
                print(f"Failed to delete employee with ID: {p_employee_id}. Response: {response}")
                return False
        else:
            print(f"Employee with ID: {p_employee_id} does not exist.")
            return False

    except Exception as e:
        print(f"An error occurred during deletion: {e}")
        return False


# In[62]:


def getDepFacet(p_collection_name):
    """
    Function to retrieve the count of employees grouped by department from the specified collection.
    
    Parameters:
    p_collection_name (str): The name of the Elasticsearch index.

    Returns:
    dict: A dictionary containing department names and their corresponding employee counts.
    """
    try:
        # Check if the index exists
        if not es.indices.exists(index=p_collection_name):
            print(f"Index '{p_collection_name}' does not exist.")
            return {}

        # Check if the index is empty
        count_response = es.count(index=p_collection_name)
        if count_response['count'] == 0:
            print(f"Index '{p_collection_name}' is empty. No employees to count.")
            return {}

        # Define the aggregation query
        query = {
            "size": 0,  # We don't need the actual documents, just the aggregation result
            "aggs": {
                "departments": {
                    "terms": {
                        "field": "Department.keyword",  # Make sure this field exists in your index mapping
                        "size": 10  # Limit the number of returned departments
                    }
                }
            }
        }

        # Perform the search query with aggregation
        response = es.search(index=p_collection_name, body=query)

        # Check the entire response structure
        print("Response received from Elasticsearch:")
        print(response)

        # Check if the aggregations key is in the response
        if 'aggregations' in response:
            if 'departments' in response['aggregations']:
                department_counts = {bucket['key']: bucket['doc_count'] for bucket in response['aggregations']['departments']['buckets']}
                
                # Log the department counts
                print("Employee count grouped by department:")
                if department_counts:
                    for dept, count in department_counts.items():
                        print(f"{dept}: {count}")
                else:
                    print("No department data found in the aggregation response.")
                
                return department_counts
            else:
                print("No 'departments' aggregation found in the response.")
                return {}
        else:
            print("No 'aggregations' key found in the response.")
            return {}

    except Exception as e:
        print(f"An error occurred during aggregation: {e}")
        return {}  # Return an empty dictionary if there's an error


# In[36]:


# Define your collection names
v_nameCollection = 'hash_rohith'  # Replace with your name
v_phoneCollection = 'hash_2075'  # Replace with your phone last four digits

# 1. Create collections
createCollection(v_nameCollection)
createCollection(v_phoneCollection)


# In[37]:


getEmpCount(v_nameCollection)


# In[47]:


indexData(v_nameCollection, 'Department')


# In[48]:


indexData(v_phoneCollection, 'Gender')


# In[52]:


# Call the function to check and delete
checkAndDeleteEmployee(v_nameCollection, 'E02003')


# In[53]:


employee_count_name_after_delete = getEmpCount(v_nameCollection)


# In[54]:


searchByColumn(v_nameCollection, 'Department', 'IT')


# In[55]:


searchByColumn(v_nameCollection, 'Gender', 'Male')


# In[56]:


searchByColumn(v_phoneCollection, 'Department', 'IT')


# In[63]:


getDepFacet(v_nameCollection)


# In[64]:


getDepFacet(v_phoneCollection)


# In[ ]:




