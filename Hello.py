# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)

#!/usr/bin/env python
# coding: utf-8

# In[15]:


# packages needed
import pandas as pd # loading the datafiles
from math import radians, sin, cos, atan2, sqrt # advanced math to calculate distance between coordinates
import openpyxl


# ### Info
# Add Vaccine info to use in the code

# In[21]:


# Shortened list of vaccines
vaccine_abbreviations = [
    "BCG",  # Bacille Calmette-Guérin
    "OPV",  # Oral Polio Vaccine
    "IPV",  # Inactivated Polio Vaccine
    "DTP",  # Diphtheria, Tetanus, Pertussis
    "HepB",  # Hepatitis B
    "MMR",  # Measles, Mumps, Rubella
    "Rotavirus",
    "PCV",  # Pneumococcal Conjugate Vaccine
    "TT",  # Tetanus Toxoid
    "YFV",  # Yellow Fever Vaccine
]

# Dictionary mapping abbreviations to full names
vaccine_dictionary = {
    "BCG": "Bacille Calmette-Guérin",
    "OPV": "Oral Polio Vaccine",
    "DTP": "Diphtheria, Tetanus, Pertussis",
    "HepB": "Hepatitis B",
    "MMR": "Measles, Mumps, Rubella",
    "Rotavirus": "Rotavirus",
    "PCV": "Pneumococcal Conjugate Vaccine",
    "IPV": "Inactivated Polio Vaccine",
    "YFV": "Yellow Fever Vaccine",
    "TT": "Tetanus Toxoid",
}

# recommended year range for each vaccine
vaccine_age_recommendations_years_int = {
    "BCG": (0, 35),
    "OPV": (0, 6),
    "DTP": (0, 2),
    "HepB": (0, 2),
    "MMR": (1, 2),
    "Rotavirus": (0, 1),
    "PCV": (0, 2),
    "IPV": (0, 2),
    "YFV": (1, 10),
    "TT": (0, 6),
}

import pandas as pd
import requests
from io import BytesIO

# URLs of the Excel files on GitHub (raw file URLs)
url1 = "https://github.com/marikolk/Vaccination/raw/main/citizens_angola_Bengo.xlsx"
url2 = "https://github.com/marikolk/Vaccination/raw/main/subset_sub-saharan_health_facilities_edited.xlsx"

# Function to read an Excel file from a URL with specified engine
def read_excel_from_url(url):
    response = requests.get(url)
    file = BytesIO(response.content)
    return pd.read_excel(file, engine='openpyxl')


# Reading the files
citizens = read_excel_from_url(url1)
hospitals = read_excel_from_url(url2)

# subsets to work with (the files i sent you guys are already subset, but keep this part of the code to showcase)
hospitals_subset = hospitals[(hospitals['Country'] == 'Angola') & (hospitals['City'] == 'Bengo')]
citizens_subset = citizens.head(500)


# ## Preparation of data
# Steps that will only be done basicly
# 
# Steps:
# 1. Function that calculates the distance between two pairs of coordinates
# 2. A loop that calculates the distances from each citizen to each hospital and store the shortest (stores both the name and the distance in KM)
# 3. Calculate number of citizens in the belonging to each hospital
# 4. Calculate the number of citizens that belong to the hospital and is in the right age range for a vaccine, then calculate number vaccinated and not vaccinated
# 

# In[28]:


# calculate distance between two pairs of coordinates
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2) + cos(radians(lat1)) * cos(radians(lat2)) * (sin(dlon / 2) ** 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Loop through citizens and find the nearest hospital, (Nearest_Hospital and Distance_to_Nearest_Hospital)
for index_citizen, citizen in citizens_subset.iterrows():
    distances = {}

    # Calculate distances for all hospitals for the current citizen
    for index_hospital, hospital in hospitals_subset.iterrows():
        distance = haversine(citizen['Lat'], citizen['Long'], hospital['Lat'], hospital['Long'])
        distances[hospital['Facility Name']] = distance

    # Find the nearest hospital for the current citizen
    min_distance_hospital = min(distances, key=distances.get)
    min_distance_value = distances[min_distance_hospital]

    # Assign the nearest hospital and distance to the citizens_subset DataFrame
    citizens_subset.at[index_citizen, 'Nearest_Hospital'] = min_distance_hospital
    citizens_subset.at[index_citizen, 'Distance_to_Nearest_Hospital'] = min_distance_value

# Count Citizens belonging to each hospital
hospitals_subset['Citizens'] = hospitals_subset['Facility Name'].apply(lambda hospital_name: citizens_subset['Nearest_Hospital'].eq(hospital_name).sum()
)

# count number of citizens in the relevant age range for each vaccine, then count number of vaccinated and not vaccinated
for vaccine, age_range in vaccine_age_recommendations_years_int.items():
    # Filter individuals within the age range for the vaccine
    eligible_individuals = citizens_subset[
        (citizens_subset['Age'] >= age_range[0]) & (citizens_subset['Age'] <= age_range[1])
    ]

    for index, hospital in hospitals_subset.iterrows():
        # Count total relevant population for the hospital
        vaccine_hospital_tot_count = len(eligible_individuals[eligible_individuals['Nearest_Hospital'] == hospital['Facility Name']])

        # Count the number of citizens who have taken the vaccine
        vaccinated_count = eligible_individuals[(eligible_individuals['Nearest_Hospital'] == hospital['Facility Name']) & (eligible_individuals[vaccine] == 1)].shape[0]

        # Count the number of citizens who have not taken the vaccine
        not_vaccinated_count = vaccine_hospital_tot_count - vaccinated_count

        # Add new columns to hospitals_subset for the current vaccine
        hospitals_subset.loc[index, f'{vaccine}_Citizen_Count'] = vaccine_hospital_tot_count
        hospitals_subset.loc[index, f'{vaccine}_Vaccinated_Count'] = vaccinated_count
        hospitals_subset.loc[index, f'{vaccine}_Not_Vaccinated_Count'] = not_vaccinated_count


# In[26]:


# here is how the df look now

# first lets check the Hospitals here we now have citizens in the rigth age range and if their vaccinated

bcg_columns = hospitals_subset.filter(like='BCG')
selected_columns = ['Country', 'City', 'Facility Name'] + list(bcg_columns.columns)
subset_with_bcg_columns = hospitals_subset[selected_columns]



# Above we see how many citizens that belongs to a hospital in the rigth age range, and also how many are vaccinated and not. The BCG vaccine with zeros is used to input how many vaccines the hospitals has and is currenly 0




# Now we can see that individuals have been assigned to their nearest hospital and the distance in KM is also listed

# ## Class Patient
# 
# Making a class that enables a few different functions
# 
# * You can inout data frames that that then is converted to a the class so that all the class functions can be used on the data frame
# * You can also add patient, update vaccine status -> this will modify the original and global DF
# * Functions like, summary etc to get vaccination status and patient info

# In[29]:


# ask for the hospital of the worker
my_hospital = 'Hospital Provincial de Bengo'
patients_subset = []
# making a class, the class can also convert df with patients/citizens
class Patient:
  all_IDs = []
  all_countries = []
  all_cities = []

  # Possible vaccines
  possible_vaccines = [v.upper() for v in vaccine_abbreviations]

  # Vaccine dictionary
  vaccine_description = vaccine_dictionary

  # default input
  def __init__(self, ID, age, gender, hospital=my_hospital, df=None):
    self.ID = ID
    self.age = age
    self.gender = gender
    self.hospital = hospital
    self.vaccine_status = {}
    Patient.all_IDs.append(ID)

    # Access DataFrame to get additional information (to have less input work from health worker)
    if df is None:
      hospital_info = hospitals_subset[hospitals_subset['Facility Name'] == hospital].iloc[0]
      self.city = hospital_info['City']
      self.country = hospital_info['Country']
      Patient.all_countries.append(hospital_info['Country'])
      Patient.all_cities.append(hospital_info['City'])
      self.add_to_citizens_subset()
    else:
      patient_info = df[df['ID'] == ID].iloc[0]
      self.city = patient_info['City']
      self.country = patient_info['Country']
      Patient.all_countries.append(patient_info['Country'])
      Patient.all_cities.append(patient_info['City'])

    # Set vaccination status based on DataFrame information
      self.set_vaccination_status_from_df(patient_info)

    patients_subset.append(self)

  def add_to_citizens_subset(self):
    global citizens_subset
    new_patient_info = {'ID': self.ID, 'Age': self.age, 'Gender': self.gender, 'City': self.city, 'Country': self.country}
    citizens_subset = citizens_subset.append(new_patient_info, ignore_index=True)

  def set_vaccination_status_from_df(self, patient_info):
    # Extract relevant columns from DataFrame
    vaccine_columns = patient_info.index[patient_info.index.isin(vaccine_abbreviations)]

    # Set vaccination status based on DataFrame information
    for vaccine in vaccine_columns:
      self.vaccine_status[vaccine.upper()] = bool(patient_info[vaccine])


  def get_vaccines_list(self):
    return self.vaccine_description

  def input_vaccination_status(self, **kwargs):
    expected_vaccines = {vaccine.upper() for vaccine in self.get_not_true_vaccines()}

    for vaccine_name, status in kwargs.items():
      if vaccine_name.upper() in expected_vaccines:
        self.vaccine_status[vaccine_name.upper()] = status
      else:
        print(f"Ignoring unknown vaccine: {vaccine_name}")

    # Update vaccination status in citizens_subset
      self.update_citizens_subset_vaccination_status()

  def update_citizens_subset_vaccination_status(self):
    global citizens_subset
    # Find the patient in citizens_subset and update their vaccination status
    row_index = citizens_subset.loc[citizens_subset['ID'] == self.ID].index[0]
    for vaccine, status in self.vaccine_status.items():
      citizens_subset.at[row_index, vaccine] = int(status)


    # get the vaccines the child has taken
  def get_true_vaccines(self):
    true_keys = []
    for key, value in self.vaccine_status.items():
      if value == True:
        true_keys.append(key)
    return true_keys

  # get the vaccines the child misses
  def get_not_true_vaccines(self):
    missing_vaccines = []
    for vaccine in self.possible_vaccines:
      if vaccine not in self.get_true_vaccines():
        missing_vaccines.append(vaccine)
      else: pass
    return missing_vaccines

  def summary(self):
    print(f'Patient with ID {self.ID} has birth gender {self.gender}. This patient has age {self.age} and lives in {self.city}.\nThe patient has at current time taken these vaccines: {self.get_true_vaccines()}\nVaccines that are missing: {self.get_not_true_vaccines()}')


# In[30]:


# adding the df to the class
patients_subset = [Patient(ID=row['ID'], age=row['Age'], gender=row['Gender'], df=citizens_subset) for _, row in citizens_subset.iterrows()]


# In[31]:


# Function to find a patient by ID
def find_patient_by_id(target_id:int, patients_list=patients_subset):
    for patient in patients_list:
        if patient.ID == target_id:
            return patient  # Return the patient instance if found
    return None  # Return None if no patient with the specified ID is found


# In[32]:


# okey lets check if the patient from the data frame we loaded is of the class Patients
cool_human =  find_patient_by_id(2)
cool_human.summary()

























################################################
######           APPLICATION              ######
################################################




# Hospital interface: Functionalities work, maybe some refinements needed but overall ok!
# Goverment interface - Option 'get a report' is almost done, Kaat will finish this today (Thursday). We need to think about the options'add citizen' and 'distribute vaccines'
# 

# In[ ]:


import streamlit as st

# Define global variables or import necessary modules here

# Function to display the initial interface
def main():
    st.header("Welcome to the AngoVaxTracker :flag-ao:", divider='rainbow')
    st.write("Please specify if you work at a hospital or for the government.")
    choice = st.selectbox("Select your workplace:", (' ','Hospital', 'Government'))

    if choice == 'Hospital':
        st.header("AngoVaxTracker :flag-ao: for Hospitals")
        hospital_menu()
    elif choice == 'Government':
        st.header("AngoVaxTracker :flag-ao: for Government")
        government_menu()

       
        
# Function to display the hospital menu
def hospital_menu():
    st.subheader("AngoVaxTracker for Hospitals")
    choice = st.radio("What would you like to do?", 
                      ('Get a report on a patient', 'Add a patient', 'Update vaccine status'))

    if choice == 'Get a report on a patient':
        get_report()
    elif choice == 'Add a patient':
        add_new_patient()
    elif choice == 'Update vaccine status':
        update_vaccine_status()

# Function for adding a new patient
def add_new_patient():
  print('I can help you with that, please provide me with ID, age and gender of the patient and the hospital you are currently at.')
  ID_exists = True

  while ID_exists == True:
    ID_input = st.number_input('ID:', step=1)

    #If the ID is already in our Patient class, then we cannot add another patient with this ID.
    if ID_input in Patient.all_IDs:
      st.warning("This ID is already registered. Please provide another ID.")
    else:
        ID_exists = False
        age_input = st.number_input('Age in whole number:', step=1)
        gender_input = st.selectbox('Select Gender:', ['F', 'M']).upper()
        hospital_input = st.text_input('The Hospital Facility Name:')
        patient_at_hand = Patient(ID=ID_input, age=age_input, gender=gender_input, hospital=hospital_input)

        # Also add vaccines for the new patient?
    st.write('Thank you. Would you also like to update the vaccine status of the patient you added?')
    update_vaccines = st.radio("Select an option:", ["Yes", "No"]).upper()

    if update_vaccines == 'YES':
        set_vaccine_status(patient_at_hand)
    # If No, we pass
    else:
        pass


# Function for updating vaccine status
def update_vaccine_status():
    st.subheader("Update Vaccine Status")
    patient_id = st.number_input("Enter the patient ID to update vaccine status:", step=1)
    # Implement logic to find patient and update status
    if st.button("Update Status"):
        st.success(f"Vaccine status updated for patient ID: {patient_id}")

# Function for getting a report
def get_report():
    st.subheader("Get a Report on a Patient")
    patient_id = st.number_input("Enter the patient ID:", min_value=0, step=1)
    find_button = st.button("Find Patient")

    if find_button:
        # Assuming 'find_patient_by_id' is a function that returns patient data or None
        patient_data = patient_id # Implement this function according to your data structure

        if patient_data:
            st.write(f'Patient with ID {patient_id} has birth gender M. This patient is 26 years old and lives in Bengo.\nThe patient has at current time taken these vaccines: HPV, OPV. \nVaccines that are missing: Rotavirus')
            patient_id = None
        else:
            st.error("Patient not found. Please try again.")

        
# Function to display the government menu
def government_menu():
    st.subheader("AngoVaxTracker for Government")
    choice = st.radio("What would you like to do?", 
                      ('Add citizens', 'Distribute vaccines', 'Get overall report', 'Show hospital map', 'Show unvaccinated population'))

    if choice == 'Add citizens':
        add_citizens()
    elif choice == 'Distribute vaccines':
        distribute_vaccines()
    elif choice == 'Get overall report':
        country_report()
    elif choice == 'Show hospital map':
        hospital_map()
    elif choice == 'Show unvaccinated population':
        unvaccinated_map()

# Example function for adding citizens (you'll need to implement the logic)
def add_citizens():
    st.write("You chose the option 'Add citizens'")
    # Implement the logic for adding citizens

# Example function for distributing vaccines (you'll need to implement the logic)
def distribute_vaccines():
    st.write("You chose the option 'Distribute vaccines'")
    # Implement the logic for distributing vaccines

# Example function for getting the overall report (you'll need to implement the logic)
import streamlit as st

def country_report():
    # Display the country
    country_input = st.selectbox(label="Choose country", options=["Angola"])
    
   
    st.subheader(f"Country Report for {country_input}")    
    
    # Calculate hospitals and cities counts
    list_hospitals = hospitals_subset[hospitals_subset['Country'] == country_input]['Facility Name'].tolist()
    hospitals_count = len(list_hospitals)
    full_list_cities = citizens_subset[citizens_subset['Country'] == country_input]['City'].tolist()
    list_cities = list(dict.fromkeys(full_list_cities))
    cities_count = len(list_cities)

    # Prepare to display vaccine coverage
    full_list_IDs = []
    vaccine_coverage_data = []

    for vaccine, age_range in vaccine_age_recommendations_years_int.items():
        eligible_individuals = citizens_subset[(citizens_subset['Age'] >= age_range[0]) & (citizens_subset['Age'] <= age_range[1]) & (citizens_subset['Country'] == country_input)]
        list_elig = eligible_individuals['ID'].tolist()
        elig_count = len(list_elig)
        elig_vaccinated = eligible_individuals[vaccine].sum()
        coverage_rate = round(elig_vaccinated / elig_count, 4) if elig_count else 0
        vaccine_coverage_data.append([vaccine, elig_vaccinated, elig_count, coverage_rate])
        full_list_IDs.extend(list_elig)

    list_IDs = list(dict.fromkeys(full_list_IDs))
    patients_count = len(list_IDs)

    vaccine_coverage_df = pd.DataFrame(vaccine_coverage_data, columns=['Vaccine', 'Eligible & Vaccinated', 'Eligible Total', 'Coverage Rate'])
    
    # Display summary information
    st.write(f"{country_input} has {cities_count} cities and {hospitals_count} hospitals.")
    st.write(f"In total, {patients_count} patients are eligible for at least one vaccine.")
    
    # Display vaccine coverage table
    st.write("Vaccine Coverage:")
    st.table(vaccine_coverage_df.set_index('Vaccine'))

    # Interactive part for more detailed report
    detailed_report = st.radio("Do you want to get a more detailed report?", 
                               ('No', 'Specify a city', 'Specify a vaccine', 'Specify a hospital'))

    if detailed_report == 'Specify a city':
        city = st.selectbox("Choose a city", list_cities)
        if city:
            city_report(city, country_input)  # Define this function

    elif detailed_report == 'Specify a vaccine':
        vaccine = st.selectbox("Choose a vaccine", list(vaccine_abbreviations.keys()))
        if vaccine:
            vaccine_report(vaccine, country_input)  # Define this function

    elif detailed_report == 'Specify a hospital':
        hospital = st.selectbox("Choose a hospital", list_hospitals)
        if hospital:
            hospital_report(hospital)  # Define this function

            
#### fancy hospital map function #####
import streamlit as st
import pandas as pd
import numpy as np

def hospital_map():
    df = pd.DataFrame({
        "col1": [-8.6560,-8.5025,-7.8522,-8.6742,-8.5835,-8.1328,-8.7131,-8.4995,-8.5824],
        "col2": [13.4918,14.5862,13.1306,14.7925,13.6569,14.2947,14.4626,14.5866,13.6594],
    })

    st.map(df,
        latitude='col1',
        longitude='col2',
        size = 1000
        )    

def unvaccinated_map():
    vaccine_choice = st.selectbox(label="Please select the vaccine.", options=['BCG', 'OPV', 'DTP', 'HepB', 'MMR', 'Rotavirus', 'PCV', 'IPV', 'YFV', 'TT'])
    map_button = st.button("View map")
    
    
    if map_button:
        unvaccinated_lat = citizens_subset[citizens_subset[vaccine_choice] == 0]['Lat'].tolist()
        unvaccinated_long = citizens_subset[citizens_subset[vaccine_choice] == 0]['Long'].tolist()
    
    df = pd.DataFrame({
        "col1": unvaccinated_lat,
        "col2": unvaccinated_long,
    })

    st.map(df,
        latitude='col1',
        longitude='col2',
        size = 100
        ) 
 
    

# Main function to run the Streamlit app
if __name__ == "__main__":
    main() 

    


# ## Going forward:
# 
# - Need the goverment interface (this will also requiere us to make some new functions) - This is the most important
# Looking to do things like #goverment_report to get the vaccination rate for a country, city and hospital
# Further it would also be cool to use the vaccination rate in cities to distribute vaccines fair and good
# 
