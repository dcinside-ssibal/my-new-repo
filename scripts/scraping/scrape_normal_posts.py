from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime, timedelta
from scripts.utils import load_login_info, setup_driver, login, load_existing_posts, save_posts

def get_normal_posts(driver, page):
    """Retrieve normal posts from the given page."""
    url = f'https://gall.dcinside.com/mgallery/board/lists?id=galaxy_tab&page={page}'
    print(f"Loading URL: {url}")
    driver.get(url)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.ub-content.us-post'))
        )
    except Exception as e:
        print(f"Error loading post list page {page}: {e}")
        print(f"Stacktrace: {e}")
        page_source = driver.page_source
        with open(f'debug_page_source_{page}.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    posts = soup.find_all('tr', class_='ub-content us-post')
    
    post_data = []
    for post in posts:
        title = post.find('td', class_='gall_tit').text.strip()
        link = post.find('td', class_='gall_tit').a['href']
        post_url = f'https://gall.dcinside.com{link}'
        time_text = post.find('td', class_='gall_date')['title'].strip()
        post_time = datetime.strptime(time_text, '%Y-%m-%d %H:%M:%S')
        writer = post.find('td', class_='gall_writer').text.strip()
        view_count = post.find('td', class_='gall_count').text.strip()
        recommend_count = post.find('td', class_='gall_recommend').text.strip()

        # 1시간 이상 지난 게시글만 선택
        if post_time < datetime.now() - timedelta(hours=1):
            post_data.append({
                'title': title,
                'url': post_url,
                'time': post_time.strftime('%Y-%m-%d %H:%M:%S'),
                'writer': writer,
                'view_count': view_count,
                'recommend_count': recommend_count
            })
    
    return post_data

def scrape_normal_posts():
    """Main function to scrape normal posts and save them."""
    user_id, user_password = load_login_info()
    driver = setup_driver()
    login(driver, user_id, user_password)

    normal_posts = load_existing_posts()
    new_posts = []
    existing_urls = [post['url'] for post in normal_posts]

    for page in range(1, 5):
        try:
            recent_posts = get_normal_posts(driver, page)
            for post in recent_posts:
                if post['url'] not in existing_urls:
                    new_posts.append(post)
        except Exception as e:
            print(f"Error while getting posts from page {page}: {e}")

    normal_posts.extend(new_posts)
    save_posts(normal_posts)

    driver.quit()
    print("Scraping and saving normal posts completed.")

if __name__ == "__main__":
    scrape_normal_posts()
