# This is Linkedin job offer scraper
# This code saves only job offers that contain specified keywords
# For the code to work, open the Chrome browser from CMD with this command:
# "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
# (Modify the route or the port if necessary)
# Then open linkedin/jobs and perform a job search
# Scroll down the list of job offers with the slider, so that all offers are loaded
# Run this code and wait for all the offers to be read
# Go to the next page with offers, scroll down again and run the code again
# Repeat untill all offers are read

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3 

# Function to read job offer content
def click_and_read_job_offer(driver, job_title_element):
    job_title_element_href = job_title_element['href']
    job_url = f"https://www.linkedin.com{job_title_element_href}"

    # Use JavaScript to open the link in a new window
    driver.execute_script(f"window.open('{job_url}');")

    # Switch to the new tab
    driver.switch_to.window(driver.window_handles[1])

    try:
        # Wait for the job offer page to load (adjust the timeout as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jobs-description-content__text"))
        )

        # Extract job description from the job offer page
        job_offer_soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_description_element = job_offer_soup.find("div", class_="jobs-description-content__text")

        if job_description_element:
            job_description = job_description_element.text.strip()[19:]
            job_description = job_description[14:].replace('\n', ' ')
            print("Job Description:", job_description)
            return job_description

    except Exception as e:
        print(f"Error waiting for element on job offer page: {e}")

    finally:
        # Close the current tab (job offer page)
        driver.close()

        # Switch back to the main window
        driver.switch_to.window(driver.window_handles[0])

    return None

# Function to calculate cosine similarity
def calculate_cosine_similarity(description1, description2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([description1, description2])
    similarity_matrix = cosine_similarity(tfidf_matrix)
    return similarity_matrix[0, 1]

remote_debugging_port = 9222  # Update with the correct port number

# Create a ChromeOptions object and specify the debugging address
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("debuggerAddress", f"localhost:{remote_debugging_port}")

# Disable popup blocking
chrome_options.add_argument("--disable-popup-blocking")

# Initialize a web driver to connect to the currently open browser
driver = webdriver.Chrome(options=chrome_options)

# Get the current page's HTML content
html_content = driver.page_source

# Parse the HTML content with Beautiful Soup
soup = BeautifulSoup(html_content, 'html.parser')

# Extract and print job titles and company names on the current page
job_card_elements = soup.find_all("div", class_="job-card-container")
new_data = set()  # Store new data to be written to the file

# Keywords to filter job titles
keywords = ['data analyst', "analista de datos", "business intelligence", 'PowerBI', 'Power BI', 'BI']

filename='job_offers_data_analytics.txt'

# Setup an SQLite DB
connection = sqlite3.connect(filename[:-8]+'.db') 
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS job_offers (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    DateAdded DATE DEFAULT CURRENT_DATE,
    Title CHAR,
    Company CHAR,
    Location CHAR,
    Description VARCHAR
);               
               ''')

# Extract company names and offers to check if they are already in the database
cursor.execute("SELECT Company, Description FROM job_offers")
existing_data = cursor.fetchall()

for job_card_element in job_card_elements:
    job_title_element = job_card_element.find("a", class_="job-card-container__link")
    company_name_element = job_card_element.find("span", class_="job-card-container__primary-description")
    location_element = job_card_element.find("li", class_="job-card-container__metadata-item")

    if job_title_element and company_name_element:
        job_title = job_title_element.text.strip()
        company_name = company_name_element.text.strip()
        location = location_element.text.strip()

        # Check if the keyword is present in the job title
        for keyword in keywords:
            if keyword.lower() in job_title.lower():
                print('Job title: ', job_title)
                print('Company name: ', company_name)
                print('Location: ', location)

                job_description = click_and_read_job_offer(driver, job_title_element)

                if job_description:
                    # Check if the company name is already in the database
                    existing_company_descriptions = [
                        (comp, desc) for comp, desc in existing_data if comp.lower() == company_name.lower()
                    ]

                    new_record = (job_title, company_name, location, job_description)
                    insertion_message = None

                    if existing_company_descriptions:
                        # Check similarity with existing job descriptions for the same company
                        for existing_company, existing_description in existing_company_descriptions:
                            similarity = calculate_cosine_similarity(existing_description, job_description)
                            if similarity >= 0.9:
                                insertion_message = "Similar job description found. Skipping insertion."
                                break
                        else:
                            insertion_message = "No similar job description found. Inserting new record."
                    else:
                        insertion_message = "Company not found in the database. Inserting new record."

                    if insertion_message and not any(record == new_record for record in new_data):
                        new_data.add(new_record)
                        with open(filename, 'a', encoding='utf-8') as file:
                            file.write(f"{job_title}\t{company_name}\t{location}\t{job_description}\n")                 
                            cursor.execute("INSERT INTO job_offers (Title, Company, Location, Description) VALUES (?, ?, ?, ?)",(job_title, company_name, location, job_description))
                            print(insertion_message)
                else:
                    print("No job description found.")
                print()

# Close the web driver when finished
driver.quit()

# Commit and close the SQLite connection
connection.commit()
connection.close()