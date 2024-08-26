# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 12:36:41 2024

@author: Hp
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Set up the WebDriver using ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def handle_cookies():
    try:
        accept_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
        )
        accept_cookies_button.click()
    except Exception as e:
        print("No cookie popup found or failed to accept cookies, continuing without action.")

def select_airport(input_element_id, airport_code):
    try:
        input_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, input_element_id))
        )
        driver.execute_script(f"document.getElementById('{input_element_id}').removeAttribute('readonly');")
        input_element.click()
        input_element.clear()
        input_element.send_keys(airport_code)
        time.sleep(2)
        input_element.send_keys(Keys.ENTER)
    except Exception as e:
        print(f"Exception during airport selection: {e}")

def select_date(date_str):
    try:
        driver.execute_script(f"document.getElementById('ddate').value = '{date_str}';")
        return True
    except Exception as e:
        print(f"Exception during date selection: {e}")
        return False

def click_search_button():
    try:
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.srchBtnSe'))
        )
        search_button.click()
    except Exception as e:
        print(f"Click failed: {e}")

def extract_flight_data():
    flight_data = []
    flights = driver.find_elements(By.CLASS_NAME, 'col-md-12.col-sm-12.main-bo-lis.pad-top-bot.ng-scope')
    for flight in flights:
        try:
            airline_name = flight.find_element(By.CLASS_NAME, 'txt-r4.ng-binding').text
            flight_number = flight.find_element(By.CLASS_NAME, 'txt-r5').text
            departure_time = flight.find_element(By.CLASS_NAME, 'txt-r2-n.ng-binding').text
            arrival_time = flight.find_elements(By.CLASS_NAME, 'txt-r2-n.ng-binding')[1].text

            price_element = flight.find_element(By.CSS_SELECTOR, 'div.txt-r6-n.exPrc span.ng-binding')
            price = price_element.text.replace(',', '').replace('₹', '').strip()

            origin = flight.find_element(By.CLASS_NAME, 'txt-r3-n.ng-binding').text
            destination = flight.find_elements(By.CLASS_NAME, 'txt-r3-n.ng-binding')[1].text

            flight_data.append({
                'Airline Name': airline_name,
                'Flight Number': flight_number,
                'Departure Time': departure_time,
                'Arrival Time': arrival_time,
                'Price': float(price),
                'Origin': origin,
                'Destination': destination,
            })
        except Exception as e:
            print(f"Failed to extract data for a flight: {e}")
    return flight_data

def get_cheapest_flights(origin, destination, travel_date):
    driver.get("https://www.easemytrip.com/")
    handle_cookies()

    try:
        select_airport('FromSector_show', origin)
        select_airport('Editbox13_show', destination)
        if not select_date(travel_date):
            return []
        click_search_button()
        time.sleep(10)

        flight_data = extract_flight_data()
        flight_data = sorted(flight_data, key=lambda x: x['Price'])[:3]
    except Exception as e:
        print(f"Exception during search: {e}")
        flight_data = []

    return flight_data

# Streamlit inputs
st.title("Cheapest Flight Finder")

origin_airport = st.text_input("Enter origin airport code (e.g., DEL)", "SXR")
destination_airport = st.text_input("Enter destination airport code (e.g., BLR)", "BLR")
travel_date = st.date_input("Select travel date", datetime.strptime("20/09/2024", "%d/%m/%Y"))
travel_date = travel_date.strftime("%d/%m/%Y")

# Button to trigger flight search
if st.button("Search for Flights"):
    try:
        st.write("Searching for flights, please wait...")
        cheapest_flights = get_cheapest_flights(origin_airport, destination_airport, travel_date)

        if cheapest_flights:
            df = pd.DataFrame(cheapest_flights)
            st.write("The three cheapest flights are:")
            st.dataframe(df)
        else:
            st.write("No flights found for the given inputs.")
    finally:
        driver.quit()
