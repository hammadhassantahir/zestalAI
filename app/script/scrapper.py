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
from ..models import User, FacebookPost, FacebookComment
from ..extensions import db
from datetime import datetime
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



def scrape_post_comments(posts):
    driver = get_driver()

    try:
        for post in posts:
            # Navigate to the starting URL
            driver.get(post.permalink_url)
            time.sleep(5)  # Allow page to load


            # ---- EXTRACT POST TEXT ----
            try:
                post_text = driver.find_element(By.XPATH, '//div[@data-ad-rendering-role="story_message"]').text
                # print(post_text)
            except:
                post_text = "Post text not found."
            # print("📝 Post text:", post_text)

            # ---- LOAD MORE COMMENTS (optional) ----
            for i in range(10):  # adjust this number for more comments
                try:
                    more_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(text(),'View more comments')]")
                    more_btn.click()
                    time.sleep(3)
                except:
                    break
            try:
                # ---- GET MAIN COMMENTS ----
                # Only get top-level comments (not replies) - they have "Comment by" but not nested in other comment divs
                comment_blocks = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Comment by") and @role="article"]')
                # print(f"Found {len(comment_blocks)} main comments")
                
                # Get all reply blocks separately for matching later
                all_replies_on_page = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Reply by") and @role="article"]')
                # print(f"Found {len(all_replies_on_page)} total reply comments on the page")
                

                print(f"Post text:{post_text} Found {len(comment_blocks)} main comments and {len(all_replies_on_page)} reply comments on the page")
                # Create a map to store comment ID to DB ID mapping
                comment_id_to_db_id = {}
                comment_name_to_db_id = {}
                
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

                    # 1️⃣ Get commenter name
                    try:
                        name_elements = comment.find_elements(By.XPATH, './/span[@dir="auto"]')
                        if name_elements:
                            comment_data["name"] = name_elements[0].text
                    except:
                        pass

                    # 2️⃣ Get comment text
                    try:
                        text_elements = comment.find_elements(
                            By.XPATH, './/div[@dir="auto" and @style="text-align: start;"]'
                        )
                        if text_elements:
                            comment_data["comment"] = text_elements[0].text
                    except:
                        pass

                    # 3️⃣ Get comment time and ID
                    try:
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

                    # 4️⃣ Get like count
                    try:
                        like_elements = comment.find_elements(
                            By.XPATH, './/div[contains(@aria-label, "reaction")]'
                        )
                        if like_elements:
                            like_aria_label = like_elements[0].get_attribute('aria-label')
                            if like_aria_label and 'reaction' in like_aria_label:
                                comment_data["likes"] = like_aria_label.split(' ')[0]
                    except:
                        pass

                    # 5️⃣ Get profile URL
                    try:
                        profile_links = comment.find_elements(
                            By.XPATH, './/a[contains(@href, "facebook.com/") and @role="link"]'
                        )
                        if profile_links:
                            profile_url = profile_links[0].get_attribute('href')
                            if profile_url:
                                comment_data["profile_url"] = profile_url.split('?')[0]
                    except:
                        pass

                    # 6️⃣ Check if liked
                    try:
                        like_buttons = comment.find_elements(
                            By.XPATH, './/div[@aria-label="Remove Like"]'
                        )
                        if like_buttons:
                            comment_data["has_liked"] = True
                    except:
                        pass

                    # 7️⃣ Get language
                    try:
                        lang_elements = comment.find_elements(
                            By.XPATH, './/span[@dir="auto" and @lang]'
                        )
                        if lang_elements:
                            comment_data["language"] = lang_elements[0].get_attribute('lang')
                    except:
                        pass
                    
                    # Save or update main comment
                    existing_comment = FacebookComment.query.filter_by(facebook_comment_id=comment_data["comment_id"]).first()
                    if existing_comment:
                        existing_comment.message = comment_data["comment"]
                        existing_comment.from_id = comment_data["name"]
                        existing_comment.from_name = comment_data["name"]
                        existing_comment.comment_date = comment_data["date"] if comment_data["date"] else 'N/A'
                        existing_comment.likes_count = comment_data["likes"] if comment_data["likes"] else 0
                        existing_comment.has_liked = True if comment_data["has_liked"] else False
                        existing_comment.language = comment_data["language"] if comment_data["language"] else None
                        existing_comment.fetched_at = datetime.utcnow()
                        db.session.commit()
                        parent_db_comment_id = existing_comment.id
                    else:
                        new_comment = FacebookComment(
                            post_id=post.id, 
                            facebook_comment_id=comment_data["comment_id"], 
                            message=comment_data["comment"], 
                            from_id=comment_data["name"], 
                            from_name=comment_data["name"], 
                            comment_date=comment_data["date"] if comment_data["date"] else 'N/A', 
                            likes_count=comment_data["likes"] if comment_data["likes"] else 0, 
                            post_url=comment_data["profile_url"] if comment_data["profile_url"] else 'N/A',
                            has_liked=True if comment_data["has_liked"] else False,
                            language=comment_data["language"] if comment_data["language"] else None,
                            fetched_at=datetime.utcnow(),
                            user_id=post.user_id
                        )
                        db.session.add(new_comment)
                        db.session.commit()
                        parent_db_comment_id = new_comment.id
                    
                    # Store mapping for later reply matching
                    if comment_data["comment_id"]:
                        comment_id_to_db_id[comment_data["comment_id"]] = parent_db_comment_id
                    if comment_data["name"]:
                        comment_name_to_db_id[comment_data["name"]] = parent_db_comment_id
                    
                    comments.append(comment_data)
                    
                    # ---- GET REPLY COMMENTS (SUB-COMMENTS) ----
                    try:
                        # Method 1: Try to find replies within the comment element
                        reply_blocks = comment.find_elements(By.XPATH, './/div[contains(@aria-label, "Reply by") and @role="article"]')
                        
                        # Method 2: If no replies found, look for them in following siblings
                        if not reply_blocks:
                            reply_blocks = comment.find_elements(By.XPATH, './following-sibling::div//div[contains(@aria-label, "Reply by") and @role="article"]')
                        
                        # Method 3: Fallback - look in descendant divs without role filter
                        if not reply_blocks:
                            reply_blocks = comment.find_elements(By.XPATH, './/div[contains(@aria-label, "Reply by")]')
                        
                        # Method 4: Look specifically for replies mentioning this commenter
                        if not reply_blocks and comment_data.get("name"):
                            reply_blocks = comment.find_elements(By.XPATH, f'.//div[contains(@aria-label, "Reply by") and contains(@aria-label, "to {comment_data["name"]}")]')
                        
                        # print(f"Found {len(reply_blocks)} replies for comment {comment_data['comment_id']}")
                        
                        for reply in reply_blocks:
                            reply_data = {
                                "name": None,
                                "comment": None,
                                "date": None,
                                "likes": "0",
                                "comment_id": None,
                                "profile_url": None,
                                "has_liked": False,
                                "language": None
                            }
                            
                            # 1️⃣ Get commenter name
                            try:
                                name_elements = reply.find_elements(By.XPATH, './/span[@dir="auto"]')
                                if name_elements:
                                    reply_data["name"] = name_elements[0].text
                            except:
                                pass
                            
                            # 2️⃣ Get reply text
                            try:
                                text_elements = reply.find_elements(
                                    By.XPATH, './/div[@dir="auto" and @style="text-align: start;"]'
                                )
                                if text_elements:
                                    reply_data["comment"] = text_elements[0].text
                            except:
                                pass
                            
                            # 3️⃣ Get reply time and ID
                            try:
                                time_links = reply.find_elements(
                                    By.XPATH, './/a[contains(@href, "comment_id") or contains(@href, "reply_comment_id")]'
                                )
                                if time_links:
                                    reply_data["date"] = time_links[0].text
                                    reply_url = time_links[0].get_attribute('href')
                                    # Try to extract reply_comment_id first, then comment_id
                                    if 'reply_comment_id=' in reply_url:
                                        reply_data["comment_id"] = reply_url.split('reply_comment_id=')[1].split('&')[0]
                                    elif 'comment_id=' in reply_url:
                                        reply_data["comment_id"] = reply_url.split('comment_id=')[1].split('&')[0]
                            except:
                                pass
                            
                            # 4️⃣ Get like count
                            try:
                                like_elements = reply.find_elements(
                                    By.XPATH, './/div[contains(@aria-label, "reaction")]'
                                )
                                if like_elements:
                                    like_aria_label = like_elements[0].get_attribute('aria-label')
                                    if like_aria_label and 'reaction' in like_aria_label:
                                        reply_data["likes"] = like_aria_label.split(' ')[0]
                            except:
                                pass
                            
                            # 5️⃣ Get profile URL
                            try:
                                profile_links = reply.find_elements(
                                    By.XPATH, './/a[contains(@href, "facebook.com/") and @role="link"]'
                                )
                                if profile_links:
                                    profile_url = profile_links[0].get_attribute('href')
                                    if profile_url:
                                        reply_data["profile_url"] = profile_url.split('?')[0]
                            except:
                                pass
                            
                            # 6️⃣ Check if liked
                            try:
                                like_buttons = reply.find_elements(
                                    By.XPATH, './/div[@aria-label="Remove Like"]'
                                )
                                if like_buttons:
                                    reply_data["has_liked"] = True
                            except:
                                pass
                            
                            # 7️⃣ Get language
                            try:
                                lang_elements = reply.find_elements(
                                    By.XPATH, './/span[@dir="auto" and @lang]'
                                )
                                if lang_elements:
                                    reply_data["language"] = lang_elements[0].get_attribute('lang')
                            except:
                                pass
                            
                            # Save or update reply comment with parent reference
                            if reply_data["comment_id"]:
                                existing_reply = FacebookComment.query.filter_by(facebook_comment_id=reply_data["comment_id"]).first()
                                if existing_reply:
                                    existing_reply.message = reply_data["comment"]
                                    existing_reply.from_id = reply_data["name"]
                                    existing_reply.from_name = reply_data["name"]
                                    existing_reply.comment_date = reply_data["date"] if reply_data["date"] else 'N/A'
                                    existing_reply.likes_count = reply_data["likes"] if reply_data["likes"] else 0
                                    existing_reply.has_liked = True if reply_data["has_liked"] else False
                                    existing_reply.language = reply_data["language"] if reply_data["language"] else None
                                    existing_reply.parent_comment_id = parent_db_comment_id
                                    existing_reply.fetched_at = datetime.utcnow()
                                    db.session.commit()
                                else:
                                    new_reply = FacebookComment(
                                        post_id=post.id,
                                        parent_comment_id=parent_db_comment_id,
                                        facebook_comment_id=reply_data["comment_id"],
                                        message=reply_data["comment"],
                                        from_id=reply_data["name"],
                                        from_name=reply_data["name"],
                                        comment_date=reply_data["date"] if reply_data["date"] else 'N/A',
                                        likes_count=reply_data["likes"] if reply_data["likes"] else 0,
                                        post_url=reply_data["profile_url"] if reply_data["profile_url"] else 'N/A',
                                        has_liked=True if reply_data["has_liked"] else False,
                                        language=reply_data["language"] if reply_data["language"] else None,
                                        fetched_at=datetime.utcnow(),
                                        user_id=post.user_id
                                    )
                                    db.session.add(new_reply)
                                    db.session.commit()
                                    # print(f"✅ Saved reply: {reply_data['comment'][:50]}...")
                    except Exception as e:
                        logging.error(f"Error getting replies for comment {comment_data.get('comment_id')}: {e}")
                        continue
                
                # ---- PROCESS ALL REPLIES FOUND ON PAGE (Alternative Method) ----
                # print(f"\n🔄 Processing {len(all_replies_on_page)} replies using page-level matching...")
                for reply_element in all_replies_on_page:
                    try:
                        reply_aria_label = reply_element.get_attribute('aria-label')
                        # print(f"Processing reply: {reply_aria_label[:100]}...")
                        
                        reply_data = {
                            "name": None,
                            "comment": None,
                            "date": None,
                            "likes": "0",
                            "comment_id": None,
                            "profile_url": None,
                            "has_liked": False,
                            "language": None,
                            "parent_name": None
                        }
                        
                        # Extract parent commenter name from aria-label
                        # Format: "Reply by [Name] to [Parent Name]'s comment [time] ago"
                        if " to " in reply_aria_label and "'s comment" in reply_aria_label:
                            parent_part = reply_aria_label.split(" to ")[1].split("'s comment")[0]
                            reply_data["parent_name"] = parent_part.strip()
                            # print(f"  Parent name from aria-label: {reply_data['parent_name']}")
                        
                        # Extract all reply data using same methods as main comments
                        # 1️⃣ Get commenter name
                        try:
                            name_elements = reply_element.find_elements(By.XPATH, './/span[@dir="auto"]')
                            if name_elements:
                                reply_data["name"] = name_elements[0].text
                        except:
                            pass
                        
                        # 2️⃣ Get reply text
                        try:
                            text_elements = reply_element.find_elements(
                                By.XPATH, './/div[@dir="auto" and @style="text-align: start;"]'
                            )
                            if text_elements:
                                reply_data["comment"] = text_elements[0].text
                        except:
                            pass
                        
                        # 3️⃣ Get reply time and ID
                        try:
                            time_links = reply_element.find_elements(
                                By.XPATH, './/a[contains(@href, "comment_id") or contains(@href, "reply_comment_id")]'
                            )
                            if time_links:
                                reply_data["date"] = time_links[0].text
                                reply_url = time_links[0].get_attribute('href')
                                if 'reply_comment_id=' in reply_url:
                                    reply_data["comment_id"] = reply_url.split('reply_comment_id=')[1].split('&')[0]
                                elif 'comment_id=' in reply_url:
                                    # For replies, there might be both comment_id and reply_comment_id
                                    all_comment_ids = reply_url.split('comment_id=')
                                    if len(all_comment_ids) > 1:
                                        reply_data["comment_id"] = all_comment_ids[-1].split('&')[0]
                        except:
                            pass
                        
                        # 4️⃣ Get like count
                        try:
                            like_elements = reply_element.find_elements(
                                By.XPATH, './/div[contains(@aria-label, "reaction")]'
                            )
                            if like_elements:
                                like_aria_label = like_elements[0].get_attribute('aria-label')
                                if like_aria_label and 'reaction' in like_aria_label:
                                    reply_data["likes"] = like_aria_label.split(' ')[0]
                        except:
                            pass
                        
                        # 5️⃣ Get profile URL
                        try:
                            profile_links = reply_element.find_elements(
                                By.XPATH, './/a[contains(@href, "facebook.com/") and @role="link"]'
                            )
                            if profile_links:
                                profile_url = profile_links[0].get_attribute('href')
                                if profile_url:
                                    reply_data["profile_url"] = profile_url.split('?')[0]
                        except:
                            pass
                        
                        # 6️⃣ Check if liked
                        try:
                            like_buttons = reply_element.find_elements(
                                By.XPATH, './/div[@aria-label="Remove Like"]'
                            )
                            if like_buttons:
                                reply_data["has_liked"] = True
                        except:
                            pass
                        
                        # 7️⃣ Get language
                        try:
                            lang_elements = reply_element.find_elements(
                                By.XPATH, './/span[@dir="auto" and @lang]'
                            )
                            if lang_elements:
                                reply_data["language"] = lang_elements[0].get_attribute('lang')
                        except:
                            pass
                        
                        # Find parent comment DB ID using parent name
                        parent_db_id = None
                        if reply_data["parent_name"] in comment_name_to_db_id:
                            parent_db_id = comment_name_to_db_id[reply_data["parent_name"]]
                            # print(f"  ✅ Matched to parent DB ID: {parent_db_id}")
                        
                        # Save or update reply comment with parent reference
                        if reply_data["comment_id"] and parent_db_id:
                            existing_reply = FacebookComment.query.filter_by(facebook_comment_id=reply_data["comment_id"]).first()
                            if existing_reply:
                                existing_reply.message = reply_data["comment"]
                                existing_reply.from_id = reply_data["name"]
                                existing_reply.from_name = reply_data["name"]
                                existing_reply.comment_date = reply_data["date"] if reply_data["date"] else 'N/A'
                                existing_reply.likes_count = reply_data["likes"] if reply_data["likes"] else 0
                                existing_reply.has_liked = True if reply_data["has_liked"] else False
                                existing_reply.language = reply_data["language"] if reply_data["language"] else None
                                existing_reply.parent_comment_id = parent_db_id
                                existing_reply.fetched_at = datetime.utcnow()
                                db.session.commit()
                                # print(f"  ✅ Updated reply: {reply_data['comment'][:50]}...")
                            else:
                                new_reply = FacebookComment(
                                    post_id=post.id,
                                    parent_comment_id=parent_db_id,
                                    facebook_comment_id=reply_data["comment_id"],
                                    message=reply_data["comment"],
                                    from_id=reply_data["name"],
                                    from_name=reply_data["name"],
                                    comment_date=reply_data["date"] if reply_data["date"] else 'N/A',
                                    likes_count=reply_data["likes"] if reply_data["likes"] else 0,
                                    post_url=reply_data["profile_url"] if reply_data["profile_url"] else 'N/A',
                                    has_liked=True if reply_data["has_liked"] else False,
                                    language=reply_data["language"] if reply_data["language"] else None,
                                    fetched_at=datetime.utcnow(),
                                    user_id=post.user_id
                                )
                                db.session.add(new_reply)
                                db.session.commit()
                                # print(f"  ✅ Saved new reply: {reply_data['comment'][:50]}...")
                        # else:
                        #     if not reply_data["comment_id"]:
                        #         print(f"  ⚠️  Skipping reply - no comment ID found")
                        #     if not parent_db_id:
                        #         print(f"  ⚠️  Skipping reply - parent not found for: {reply_data['parent_name']}")
                    
                    except Exception as e:
                        logging.error(f"Error processing page-level reply: {e}")
                        continue
                        
            except Exception as e:
                logging.error(f"Error getting comments: {e}")
                continue

        return {'success': True}
    except Exception as e:
        logging.error(f"Error navigating to URL: {e}")
        return {'error': str(e)}
    finally:
        driver.quit()


