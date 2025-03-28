import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
import pandas as pd
from urllib.parse import urljoin
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Set up Google Gemini API
GEMINI_API_KEY = os.getenv('GEM_API')  
genai.configure(api_key=GEMINI_API_KEY)

def get_relevant_links(session, base_url, keywords, visited=set()):
    """ Collects links that might contain answers based on keywords. """
    relevant_links = set()
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        response = session.get(base_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to access {base_url} with status code: {response.status_code}")
            return relevant_links
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            url = urljoin(base_url, link['href'])
            if base_url in url and url not in visited:
                visited.add(url)
                if any(keyword.lower() in link.get_text().lower() for keyword in keywords):
                    relevant_links.add(url)
    except Exception as e:
        print(f"Error fetching links from {base_url}: {e}")
    
    return relevant_links

def extract_text_from_url(session, url):
    """ Extracts text content from a given URL """
    try:
        time.sleep(1)  
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to access {url} with status code: {response.status_code}")
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return '\n'.join([p.get_text() for p in soup.find_all('p')])
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return ""

def get_answers_from_gemini(content, questions):
    """ Sends extracted content and questions to Gemini API and gets responses """
    if not content.strip():
        return "No relevant content found on the websites."
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f"Here is some text data:\n{content}\n\nAnswer the following questions:\n" + "\n".join(questions))
        return response.text if response else "No response from Gemini API"
    except Exception as e:
        print("Error with Gemini API:", e)
        return "Gemini API failed to respond."

websites = ["https://www.3m.com" , "https://www.paypal.com" , "https://www.sap.com" , "https://global.honda" , "https://www.hyundai.com"]  # Replace with your list of websites
questions = [
    "What is the company's mission statement or core values?",
	"What products or services does the company offer?",
	"When was the company founded, and who were the founders?",
	"Where is the company's headquarters located?",
	"Who are the key executives or leadership team members?",
	"Has the company received any notable awards or recognitions?"
]


keywords = set(word.lower() for q in questions for word in q.split())

start_time = time.time() # Measuring time to see how much time it takes to complete

all_content = ""

with requests.Session() as session:
    for site in websites:
        relevant_links = get_relevant_links(session, site, keywords)
        if not relevant_links:
            all_content += extract_text_from_url(session, site) + "\n"
        else:
            for link in relevant_links:
                all_content += extract_text_from_url(session, link) + "\n"

answers = get_answers_from_gemini(all_content, questions)
print(f"Answer: {answers}")

data = {"Question": questions, "Answer": answers}
with open("answers.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


df = pd.read_json("answers.json")
df.to_csv("answers.csv", index=False)



end_time = time.time()
print(f"Execution time: {end_time - start_time:.2f} seconds")

 