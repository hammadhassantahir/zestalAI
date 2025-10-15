import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from flask import Response
from urllib.parse import urljoin, urlparse, quote

# ---- CONFIG ----
FB_POST_URL = "https://www.facebook.com/2309878802795671/posts/2319112888538929"


def get_driver():
    """
    Create and return a configured Selenium WebDriver
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)



def runScrapper(PostURL):
    driver = get_driver()

    
    try:
        # Navigate to the starting URL
        driver.get(PostURL)
        time.sleep(5)  # Allow page to load


        # ---- EXTRACT POST TEXT ----
        try:
            post_text = driver.find_element(By.XPATH, '//div[@data-ad-rendering-role="story_message"]').text
            print(post_text)
        except:
            post_text = "Post text not found."

        print("📝 Post text:", post_text)

        # ---- LOAD MORE COMMENTS (optional) ----
        for i in range(3):  # adjust this number for more comments
            try:
                more_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(text(),'View more comments')]")
                more_btn.click()
                time.sleep(3)
            except:
                break


        try:
            # ---- GET COMMENTS ----
            comment_blocks = driver.find_elements(
                By.XPATH, '//div[contains(@aria-label, "Comment by")]'
            )

            print(f"Found {len(comment_blocks)} comments")

            comments = []

            for comment in comment_blocks:
                comment_data = {
                    "name": None,
                    "comment": None,
                    "date": None,
                    "likes": "0",
                    "comment_id": None,
                    "profile_url": None,
                    "has_liked": False,
                    "language": None
                }

                try:
                    # 1️⃣ Get commenter name
                    name_elements = comment.find_elements(By.XPATH, './/span[@dir="auto"]')
                    if name_elements:
                        comment_data["name"] = name_elements[0].text
                except:
                    pass

                try:
                    # 2️⃣ Get comment text
                    text_elements = comment.find_elements(
                        By.XPATH, './/div[@dir="auto" and @style="text-align: start;"]'
                    )
                    if text_elements:
                        comment_data["comment"] = text_elements[0].text
                except:
                    pass

                try:
                    # 3️⃣ Get comment time and ID
                    time_links = comment.find_elements(
                        By.XPATH, './/a[contains(@href, "comment_id")]'
                    )
                    if time_links:
                        comment_data["date"] = time_links[0].text
                        comment_url = time_links[0].get_attribute('href')
                        if 'comment_id=' in comment_url:
                            comment_data["comment_id"] = comment_url.split('comment_id=')[1].split('&')[0]
                except:
                    pass

                try:
                    # 4️⃣ Get like count
                    like_elements = comment.find_elements(
                        By.XPATH, './/div[contains(@aria-label, "reaction")]'
                    )
                    if like_elements:
                        like_aria_label = like_elements[0].get_attribute('aria-label')
                        if like_aria_label and 'reaction' in like_aria_label:
                            comment_data["likes"] = like_aria_label.split(' ')[0]
                except:
                    pass

                try:
                    # 5️⃣ Get profile URL
                    profile_links = comment.find_elements(
                        By.XPATH, './/a[contains(@href, "facebook.com/") and @role="link"]'
                    )
                    if profile_links:
                        profile_url = profile_links[0].get_attribute('href')
                        if profile_url:
                            comment_data["profile_url"] = profile_url.split('?')[0]
                except:
                    pass

                try:
                    # 6️⃣ Check if liked
                    like_buttons = comment.find_elements(
                        By.XPATH, './/div[@aria-label="Remove Like"]'
                    )
                    if like_buttons:
                        comment_data["has_liked"] = True
                except:
                    pass

                try:
                    # 7️⃣ Get language
                    lang_elements = comment.find_elements(
                        By.XPATH, './/span[@dir="auto" and @lang]'
                    )
                    if lang_elements:
                        comment_data["language"] = lang_elements[0].get_attribute('lang')
                except:
                    pass

                comments.append(comment_data)

            for c in comments:
                print(c)
            print(f"Found {len(comments)} comments with full details****")
            return {'success': True, 'comments': comments}
            
        except Exception as e:
            logging.error(f"Error getting comments: {e}")
            return {'error': str(e)}

        
        # try:
        #     # ---- GET COMMENTS ----
        #     comment_blocks = driver.find_elements(
        #         By.XPATH, '//div[contains(@aria-label, "Comment by")]'
        #     )

        #     print(f"Found {len(comment_blocks)} comments")

        #     comments = []

        #     for comment in comment_blocks:
        #         try:
        #             # 1️⃣ Get commenter name
        #             name = comment.find_element(By.XPATH, './/span[@dir="auto"]').text
        #         except:
        #             name = None

        #         try:
        #             # 2️⃣ Get comment text (inside <div dir="auto" style="text-align: start;">)
        #             text = comment.find_element(
        #                 By.XPATH, './/div[@dir="auto" and @style="text-align: start;"]'
        #             ).text
        #         except:
        #             text = None

        #         try:
        #             # 5️⃣ Get comment time label (e.g., "2d", "3h")
        #             time_label = comment.find_element(
        #                 By.XPATH, './/a[contains(@aria-label, "ago") or contains(text(), "d") or contains(text(), "h")]'
        #             ).text
        #         except:
        #             time_label = None

        #         comments.append({
        #             "name": name,
        #             "comment": text,
        #             "date": time_label
        #         })

        #     for c in comments:
        #         print(c)
        #     print(f"Found {len(comments)} comments****")
        #     return {'success': True, 'comments': comments}
        # except Exception as e:
        #     logging.error(f"Error getting comments: {e}")
        #     return {'error': str(e)}
    except Exception as e:
        logging.error(f"Error navigating to URL: {e}")
        return {'error': str(e)}
        return {'success': True}    
    finally:
        driver.quit()

