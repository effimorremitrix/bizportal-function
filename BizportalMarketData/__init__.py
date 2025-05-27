import logging
import azure.functions as func
import requests
from bs4 import BeautifulSoup

def extract_security_identifier(user_query):
    # Simple placeholder; real implementation might use regex or NLP
    return user_query.strip()

def scrape_general_info(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        info_section = soup.find('div', class_='paperHeaderContent')
        return info_section.get_text(strip=True) if info_section else "לא נמצאה סקירה כללית."
    except Exception as e:
        return f"שגיאה בגישה לנתונים כלליים: {str(e)}"

def scrape_holdings(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup.get_text(strip=True)[:1000]  # Limit for brevity
    except Exception as e:
        return f"שגיאה בשליפת אחזקות: {str(e)}"

def scrape_performance(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup.get_text(strip=True)[:1000]
    except Exception as e:
        return f"שגיאה בביצועים: {str(e)}"

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing Bizportal market data request.')
    user_query = req.get_json().get("user_query")

    security_identifier = extract_security_identifier(user_query)
    if not security_identifier:
        return func.HttpResponse("על איזה נייר ערך תרצה מידע? אנא ציין את שמו או מספרו.", status_code=200)

    search_url = f"https://www.bizportal.co.il/tradedata/paperslist?q={security_identifier}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    first_result = soup.select_one("a.link-papers")
    if not first_result:
        return func.HttpResponse("לא מצאתי תוצאה תואמת לשם שסיפקת.", status_code=200)

    href = first_result['href']

    if "/bonds/" in href:
        section = "bonds/quote"
    elif "/foreign/stock/" in href:
        section = "foreign/stock"
    elif "/mutualfunds/" in href:
        section = "mutualfunds/quote"
    elif "/forex/etf/" in href:
        section = "forex/etf"
    elif "/tradedfund/" in href:
        section = "tradedfund/quote"
    elif "/derivatives/" in href:
        section = "derivatives/quote"
    else:
        return func.HttpResponse("לא זוהה סוג נייר ערך.", status_code=200)

    id_code = href.split("/")[-1]
    generalview_url = f"https://www.bizportal.co.il/{section}/generalview/{id_code}"
    summary_data = scrape_general_info(generalview_url)

    if "אחזקות" in user_query:
        tab_url = f"https://www.bizportal.co.il/{section}/quote/holdings/{id_code}"
        return func.HttpResponse(scrape_holdings(tab_url), status_code=200)

    if "תשואה" in user_query or "ביצועים" in user_query:
        tab_url = f"https://www.bizportal.co.il/{section}/quote/performance/{id_code}"
        return func.HttpResponse(scrape_performance(tab_url), status_code=200)

    return func.HttpResponse(summary_data, status_code=200)
