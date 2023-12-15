# This is a development file
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
            job_description = job_description.replace('\n', ' ')
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
                    new_data.add((job_title, company_name, location, job_description))
                    with open('job_offers_data_analytics.txt', 'a', encoding='utf-8') as file:
                        file.write(f"{job_title}\t{company_name}\t{location}\t{job_description}\n")

                print()

# Close the web driver when finished
driver.quit()
