import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import validators
from urllib.parse import quote
import sys
import time
import re
import logging
import random
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    filename="paywall_bypass.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def validate_url(url):
    """Validate if the URL is safe and uses HTTPS."""
    if not validators.url(url):
        logging.warning(f"Invalid URL: {url}")
        return False
    if not url.startswith("https://"):
        logging.warning(f"Non-HTTPS URL rejected: {url}")
        return False
    return True

def extract_doi(doi_input):
    """Extract DOI identifier from a full DOI URL or plain DOI."""
    doi_pattern = r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)"
    match = re.search(doi_pattern, doi_input, re.I)
    if match:
        return match.group(1)
    return None

def retry_request(url, headers=None, retries=7, backoff=10):
    """Retry HTTP requests with exponential backoff and User-Agent rotation."""
    headers = headers or {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        ])
    }
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            print(f"{Fore.RED}🔴 Request failed for {url}: {e}")
            if i == retries - 1:
                return None
            time.sleep(backoff ** i)
    return None

def query_unpaywall(doi):
    """Query Unpaywall API for open-access versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Unpaywall for DOI: {doi}")
    logging.info(f"Querying Unpaywall for DOI: {doi}")
    api_url = f"https://api.unpaywall.org/v2/{doi}?email=bihov19201@cavoyar.com"
    response = retry_request(api_url)
    if response:
        try:
            data = response.json()
            if data.get("is_oa") and data.get("best_oa_location"):
                url = data["best_oa_location"].get("url")
                if url and validate_url(url):
                    logging.info(f"Found Unpaywall PDF: {url}")
                    print(f"{Fore.GREEN}✅ Found Unpaywall PDF: {url}")
                    return url
        except ValueError as e:
            logging.error(f"Unpaywall JSON parsing error: {e}")
            print(f"{Fore.RED}🔴 Unpaywall JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Unpaywall PDF found")
    return None

def search_google_scholar(doi):
    """Search Google Scholar for alternative article versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Searching Google Scholar for DOI: {doi}")
    logging.info(f"Searching Google Scholar for DOI: {doi}")
    query = f"https://scholar.google.com/scholar?q={quote(doi)}"
    response = retry_request(query)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Google Scholar results")
        return None
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".pdf") and validate_url(href):
                logging.info(f"Found PDF on Google Scholar: {href}")
                print(f"{Fore.GREEN}✅ Found Google Scholar PDF: {href}")
                return href
            if "pdf" in href.lower() and validate_url(href):
                logging.info(f"Found potential PDF on Google Scholar: {href}")
                print(f"{Fore.GREEN}✅ Found potential Google Scholar PDF: {href}")
                return href
    except Exception as e:
        logging.error(f"Google Scholar parsing error: {e}")
        print(f"{Fore.RED}🔴 Google Scholar parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Google Scholar PDF found")
    return None

def check_wayback_machine(doi):
    """Check Wayback Machine for cached article versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Checking Wayback Machine for DOI: {doi}")
    logging.info(f"Checking Wayback Machine for DOI: {doi}")
    doi_url = f"https://doi.org/{doi}"
    wayback_url = f"https://archive.org/wayback/available?url={quote(doi_url)}"
    response = retry_request(wayback_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Wayback Machine results")
        return None
    try:
        data = response.json()
        if data.get("archived_snapshots", {}).get("closest", {}).get("url"):
            archived_url = data["archived_snapshots"]["closest"]["url"]
            if validate_url(archived_url):
                logging.info(f"Found archived version: {archived_url}")
                print(f"{Fore.GREEN}✅ Found archived version: {archived_url}")
                return archived_url
    except ValueError as e:
        logging.error(f"Wayback Machine JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 Wayback Machine JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Wayback Machine archive found")
    return None

def query_biorxiv(doi):
    """Query bioRxiv for article by DOI."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying bioRxiv for DOI: {doi}")
    logging.info(f"Querying bioRxiv for DOI: {doi}")
    api_url = f"https://api.biorxiv.org/details/biorxiv/{quote(doi)}"
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No bioRxiv results")
        return None
    try:
        data = response.json()
        if data.get("collection") and data["collection"][0].get("pdf_url"):
            pdf_url = data["collection"][0]["pdf_url"]
            if validate_url(pdf_url):
                logging.info(f"Found bioRxiv PDF: {pdf_url}")
                print(f"{Fore.GREEN}✅ Found bioRxiv PDF: {pdf_url}")
                return pdf_url
    except ValueError as e:
        logging.error(f"bioRxiv JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 bioRxiv JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No bioRxiv PDF found")
    return None

def query_core(doi):
    """Query CORE API for open-access articles."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying CORE for DOI: {doi}")
    logging.info(f"Querying CORE for DOI: {doi}")
    api_key = "your_core_api_key"  # Replace with your CORE API key
    headers = {"Authorization": f"Bearer {api_key}"}
    api_url = f"https://api.core.ac.uk/v3/search/works/?q=doi:{quote(doi)}"
    response = retry_request(api_url, headers=headers)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No CORE results")
        return None
    try:
        data = response.json()
        if data.get("results"):
            for result in data["results"]:
                if result.get("downloadUrl") and validate_url(result["downloadUrl"]):
                    logging.info(f"Found CORE PDF: {result['downloadUrl']}")
                    print(f"{Fore.GREEN}✅ Found CORE PDF: {result['downloadUrl']}")
                    return result["downloadUrl"]
    except ValueError as e:
        logging.error(f"CORE JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 CORE JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No CORE PDF found")
    return None

def query_zenodo(doi):
    """Query Zenodo for article by DOI."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Zenodo for DOI: {doi}")
    logging.info(f"Querying Zenodo for DOI: {doi}")
    api_url = f"https://zenodo.org/api/records?q=doi:{quote(doi)}"
    response = retry_request(api_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No Zenodo results")
        return None
    try:
        data = response.json()
        if data.get("hits", {}).get("hits"):
            for record in data["hits"]["hits"]:
                if record.get("files"):
                    for file in record["files"]:
                        if file.get("links", {}).get("self") and validate_url(file["links"]["self"]):
                            logging.info(f"Found Zenodo PDF: {file['links']['self']}")
                            print(f"{Fore.GREEN}✅ Found Zenodo PDF: {file['links']['self']}")
                            return file["links"]["self"]
    except ValueError as e:
        logging.error(f"Zenodo JSON parsing error: {e}")
        print(f"{Fore.RED}🔴 Zenodo JSON parsing error: {e}")
    print(f"{Fore.YELLOW}⚠️ No Zenodo PDF found")
    return None

def scrape_researchgate(doi):
    """Scrape ResearchGate for article using Selenium."""
    print(f"{Fore.CYAN}🕵️‍♂️ Scraping ResearchGate for DOI: {doi}")
    logging.info(f"Scraping ResearchGate for DOI: {doi}")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(120)
        driver.set_script_timeout(120)
    except Exception as e:
        logging.error(f"Selenium initialization error: {e}")
        print(f"{Fore.RED}🔴 Selenium initialization error: {e}")
        return None
    query = f"https://www.researchgate.net/search/publication?q={quote(doi)}"
    try:
        driver.get(query)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "publication" in href and validate_url(href):
                driver.get(href)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
                time.sleep(3)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                pdf_link = soup.find("a", href=True, string=re.compile("PDF|Download|Full-text|View", re.I))
                if pdf_link and validate_url(pdf_link["href"]):
                    logging.info(f"Found ResearchGate PDF: {pdf_link['href']}")
                    print(f"{Fore.GREEN}✅ Found ResearchGate PDF: {pdf_link['href']}")
                    driver.quit()
                    return pdf_link["href"]
        driver.quit()
        print(f"{Fore.YELLOW}⚠️ No ResearchGate PDF found")
        return None
    except Exception as e:
        logging.error(f"ResearchGate scraping error: {e}")
        print(f"{Fore.RED}🔴 ResearchGate scraping error: {e}")
        driver.quit()
        return None

def scrape_acs(doi):
    """Scrape ACS Publications for open-access versions."""
    print(f"{Fore.CYAN}🕵️‍♂️ Scraping ACS Publications for DOI: {doi}")
    logging.info(f"Scraping ACS Publications for DOI: {doi}")
    acs_url = f"https://pubs.acs.org/doi/{doi}"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(120)
        driver.set_script_timeout(120)
    except Exception as e:
        logging.error(f"ACS Selenium initialization error: {e}")
        print(f"{Fore.RED}🔴 ACS Selenium initialization error: {e}")
        return None
    try:
        driver.get(acs_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(("tag name", "body")))
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pdf_link = soup.find("a", href=True, string=re.compile("PDF|Download|Full Text|Open Access|Supporting Information", re.I))
        if pdf_link:
            href = pdf_link["href"]
            if not href.startswith("http"):
                href = f"https://pubs.acs.org{href}"
            if validate_url(href):
                logging.info(f"Found ACS PDF: {href}")
                print(f"{Fore.GREEN}✅ Found ACS PDF: {href}")
                driver.quit()
                return href
        driver.quit()
        print(f"{Fore.YELLOW}⚠️ No ACS PDF found")
        return None
    except Exception as e:
        logging.error(f"ACS scraping error: {e}")
        print(f"{Fore.RED}🔴 ACS scraping error: {e}")
        driver.quit()
        return None

def search_author_profiles(doi):
    """Search for author-uploaded versions via Google."""
    print(f"{Fore.CYAN}🕵️‍♂️ Searching author profiles for DOI: {doi}")
    logging.info(f"Searching author profiles for DOI: {doi}")
    query = f"site:*.edu | site:researchgate.net | site:academia.edu {doi} filetype:pdf"
    search_url = f"https://www.google.com/search?q={quote(query)}"
    response = retry_request(search_url)
    if not response:
        print(f"{Fore.YELLOW}⚠️ No author profile results")
        return None
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]
            if href.endswith(".pdf") and validate_url(href):
                logging.info(f"Found author-uploaded PDF: {href}")
                print(f"{Fore.GREEN}✅ Found author-uploaded PDF: {href}")
                return href
    except Exception as e:
        logging.error(f"Author profile search error: {e}")
        print(f"{Fore.RED}🔴 Author profile search error: {e}")
    print(f"{Fore.YELLOW}⚠️ No author-uploaded PDF found")
    return None

def query_scihub(doi):
    """Query Sci-Hub mirrors for article (use with caution)."""
    print(f"{Fore.CYAN}🕵️‍♂️ Querying Sci-Hub for DOI: {doi} (use with caution)")
    logging.info(f"Querying Sci-Hub for DOI: {doi}")
    scihub_urls = [
        "https://sci-hub.se",
        "https://sci-hub.st",
        "https://sci-hub.ru"
    ]
    for base_url in scihub_urls:
        url = f"{base_url}/{doi}"
        response = retry_request(url)
        if response:
            try:
                soup = BeautifulSoup(response.text, "html.parser")
                pdf_link = soup.find("a", href=True, attrs={"onclick": re.compile("location.href")})
                if pdf_link:
                    href = pdf_link["href"]
                    if not href.startswith("http"):
                        href = f"https:{href}"
                    if validate_url(href):
                        logging.info(f"Found Sci-Hub PDF: {href}")
                        print(f"{Fore.GREEN}✅ Found Sci-Hub PDF: {href}")
                        return href
            except Exception as e:
                logging.error(f"Sci-Hub parsing error for {base_url}: {e}")
                print(f"{Fore.RED}🔴 Sci-Hub parsing error for {base_url}: {e}")
    print(f"{Fore.YELLOW}⚠️ No Sci-Hub PDF found. Sci-Hub access may have legal implications.")
    logging.warning("Sci-Hub access may have legal implications. Use institutional access if possible.")
    return None

def find_article(doi):
    """Main function to find article using aggressive techniques."""
    logging.info(f"Starting search for DOI: {doi}")
    print(f"{Fore.BLUE}🔍 Searching for article with DOI: {doi}")
    
    # Check Unpaywall
    unpaywall_url = query_unpaywall(doi)
    if unpaywall_url:
        return unpaywall_url

    # Check Google Scholar
    scholar_url = search_google_scholar(doi)
    if scholar_url:
        return scholar_url

    # Check Wayback Machine
    wayback_url = check_wayback_machine(doi)
    if wayback_url:
        return wayback_url

    # Check bioRxiv
    biorxiv_url = query_biorxiv(doi)
    if biorxiv_url:
        return biorxiv_url

    # Check CORE
    core_url = query_core(doi)
    if core_url:
        return core_url

    # Check Zenodo
    zenodo_url = query_zenodo(doi)
    if zenodo_url:
        return zenodo_url

    # Check ResearchGate
    rg_url = scrape_researchgate(doi)
    if rg_url:
        return rg_url

    # Check ACS Publications
    acs_url = scrape_acs(doi)
    if acs_url:
        return acs_url

    # Search author profiles
    author_url = search_author_profiles(doi)
    if author_url:
        return author_url

    # Query Sci-Hub (last resort)
    scihub_url = query_scihub(doi)
    if scihub_url:
        return scihub_url

    print(f"{Fore.RED}❌ No accessible version found. Try contacting the author or using institutional access.")
    logging.info(f"No accessible version found for DOI: {doi}")
    return None

def main():
    print(f"{Fore.BLUE}📝 Enter the DOI URL or DOI (e.g., https://doi.org/10.1000/xyz123 or 10.1000/xyz123):")
    doi_input = input().strip()
    doi = extract_doi(doi_input)
    if not doi:
        print(f"{Fore.RED}❌ Invalid DOI format. Example: https://doi.org/10.1000/xyz123 or 10.1000/xyz123")
        logging.error(f"Invalid DOI input: {doi_input}")
        sys.exit(1)
    
    result = find_article(doi)
    if result:
        print(f"{Fore.GREEN}🎉 Success! Access the article at: {result}")
        logging.info(f"Success! Found article at: {result}")
    else:
        print(f"{Fore.RED}❌ Failed to find an accessible version.")
        logging.info("Failed to find an accessible version.")

if __name__ == "__main__":
    main()