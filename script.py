import json
import time
import random
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from threading import Thread
from bs4 import BeautifulSoup
import os
import requests
import datetime

SECONDS = datetime.datetime.now()
MSECONDS = SECONDS.microsecond * 10000


def remove_special_characters(text):
    pattern = r"['\"!@#$%^&*()<>?/\|}{~:]"
    return re.sub(pattern, '', text)


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def scrape_posts():
    URL = input("Enter community SAP category URL to scrape: ")
    scrape_post_url = True  # Assuming this is always True, as there's no option to disable it in GUI
    scrape_desc_images = True  # Assuming this is always True, as there's no option to disable it in GUI
    scrape_answer_images = True  # Assuming this is always True, as there's no option to disable it in GUI
    scrape_links_in_answer = True  # Assuming this is always True, as there's no option to disable it in GUI

    def scraping_process():
        try:
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
            driver.get(URL)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h3/a")))
            time.sleep(random.uniform(1, 2))
            driver.find_element(By.XPATH, "//li[@data-tab-setting-filters='solved']").click()

            for _ in range(5):
                try:
                    load_more_button = driver.find_element(By.XPATH, "//a[@id='theme-lib-loader-button']")
                    load_more_button.click()

                    time.sleep(random.uniform(1, 2))  # Adjust this wait time as necessary
                except Exception as e:
                    print("Exception occurred while clicking 'Load More' button:", e)
                    break

            post_links = driver.find_elements(By.XPATH, '//h3/a')
            post_urls = [link.get_attribute('href') for link in post_links]

            if scrape_desc_images:
                desc_images_folder = 'description_images'
                create_folder(desc_images_folder)

            if scrape_answer_images:
                answer_images_folder = 'answer_images'
                create_folder(answer_images_folder)

            posts_data = []
            total_posts = len(post_urls)

            for i, post_url in enumerate(post_urls, 1):
                post_data = {}

                driver.get(post_url)
                time.sleep(random.uniform(1, 2))

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'lia-message-body-content')))
                desc_element = driver.find_element(By.XPATH, "(//div[contains(@class,'lia-qa-content')])[2]")
                title_element = driver.find_element(By.XPATH, "(//div[contains(@class,'lia-qa-content')])[1]")

                desc_html = desc_element.get_attribute('innerHTML')
                desc_text = BeautifulSoup(desc_html, 'html.parser').get_text().strip()
                title = title_element.text.strip()

                title = remove_special_characters(title)

                try:
                    answer_elements = driver.find_elements(By.XPATH, "(//div[contains(@class,'lia-qa-content')])[position() > 2]")
                    answers = []
                    for answer_element in answer_elements:
                        answer_html = answer_element.get_attribute('innerHTML')
                        answer = re.sub('<[^<]+?>', '', answer_html)
                        soup = BeautifulSoup(answer_html, 'html.parser')
                        links_in_answer = [a['href'] for a in soup.find_all('a', href=True)]

                        if scrape_answer_images:
                            answer_images = answer_element.find_elements(By.TAG_NAME, 'img')
                            img_names = []
                            answer_with_image_names = answer_html  # Initialize with original HTML

                            for idx, img in enumerate(answer_images):
                                timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
                                random_number = random.randint(1, 10000)  # Generate a random number between 1 and 10000
                                img_name = f"{timestamp}_{random_number}_{idx}"  # Combine timestamp, random number, and index
                                img_name = img_name.replace("'", "")  # Remove single quotes

                                img_url = img.get_attribute('src')
                                img_url = img_url.split('?')[0]
                                img_url = img_url.replace('image-size/medium', '')
                                img_data = requests.get(img_url).content
                                with open(f'{answer_images_folder}/{img_name}.jpg', 'wb') as handler:
                                    handler.write(img_data)
                                img_names.append(img_name)

                                # Create modified image tag with 'Name' added
                                modified_img_tag = f" (Image: [{img_name}])"
                                answer_with_image_names = answer_with_image_names.replace(img.get_attribute('outerHTML'), modified_img_tag)

                            # Update the answer text with modified HTML
                            answer = BeautifulSoup(answer_with_image_names, 'html.parser').get_text().strip()
                            answers.append(answer)
                            post_data["answer_image_names"] = img_names

                        if scrape_links_in_answer:
                            post_data["links_in_answer"] = links_in_answer

                    if answers:
                        post_data["answers"] = answers

                    # Scraping comments
                    try:
                        comment_button = driver.find_element(By.XPATH, "(//a[contains(@class, 'comment-action-link')])[3]")
                        comment_button.click()
                        time.sleep(random.uniform(1, 2))
                        comment_element = driver.find_element(By.XPATH, "(//div[@class='lia-message-body-content'])[3]")
                        comments = comment_element.text.strip()
                        post_data["comments"] = comments
                    except NoSuchElementException:
                        print("")

                except NoSuchElementException:
                    print("")

                if scrape_desc_images:
                    desc_images = desc_element.find_elements(By.TAG_NAME, 'img')
                    img_names = []
                    description_with_images = desc_html  # Initialize with original HTML

                    # New list to store modified image tags
                    modified_image_tags = []

                    for idx, img in enumerate(desc_images):
                        timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
                        random_number = random.randint(1, 10000)  # Generate a random number between 1 and 10000
                        img_name = f"{timestamp}_{random_number}_{idx}"  # Combine timestamp, random number, and index
                        img_name = img_name.replace("'", "")  # Remove single quotes

                        img_url = img.get_attribute('src')
                        img_url = img_url.split('?')[0]
                        img_url = img_url.replace('image-size/medium', '')
                        img_data = requests.get(img_url).content
                        with open(f'{desc_images_folder}/{img_name}.jpg', 'wb') as handler:
                            handler.write(img_data)

                        # Create modified image tag with 'Name' added
                        modified_img_tag = f" (Image: [{img_name}])"
                        modified_image_tags.append(modified_img_tag)

                    if modified_image_tags:  # Check if there are modified image tags
                        # Replace image tags in description HTML with modified ones
                        for idx, img in enumerate(desc_images):
                            description_with_images = description_with_images.replace(img.get_attribute('outerHTML'), modified_image_tags[idx])

                        # Update the description text with modified HTML
                        desc_text = BeautifulSoup(description_with_images, 'html.parser').get_text().strip()

                    post_data["description"] = desc_text  # Store the modified description with embedded image names
                    post_data["description_image_names"] = img_names  # Store image names list in post_data dictionary

                # Remove special characters from answer text
                answers = [remove_special_characters(answer) for answer in answers]

                post_data.update({
                    "title": title,
                    "desc_images": img_names,
                })

                if scrape_post_url:
                    post_data["post-url"] = post_url

                # Append post_data to posts_data list
                posts_data.append(post_data)

            with open('posts_data.json', 'w') as json_file:
                json.dump(posts_data, json_file, indent=4)

            print("Scraping Complete")
            driver.close()

        except Exception as e:
            print("An error occurred:", e)

        finally:
            driver.quit()

    t = Thread(target=scraping_process)
    t.start()


scrape_posts()
