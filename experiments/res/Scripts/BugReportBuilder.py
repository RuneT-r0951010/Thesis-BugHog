from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import os


# Set up Chrome WebDriver (change path to chromedriver)
chrome_driver_path = "/opt/homebrew/bin/chromedriver"
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run without opening a browser

exclude_bugs = ["f1416045", "f1208559", "f784158", "f774136", "f910139", "c411600", "f1296976", "f908933", "f908824", "c1248289", "c393401", "c661852", "f1073952", "c487155", "f1460538"]
allowed_extensions = [".html", ".py", ".js", ".txt", ".php"]


class BugReportBuilder:
    def __init__(self, use_urls: bool = False):
        self.use_urls = use_urls
        self.report_path = lambda bug_id: f"Reports/{bug_id}.txt"

    # Scrape and return the bug report for a given bug_id
    def scrape_bug_report(self, bug_id, save_scraped_content = False):
        if (bug_id not in exclude_bugs and "-" not in bug_id):
            # driver = webdriver.Chrome(service=service, options=options)
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            bug_id_prefix = bug_id[0]

            scraped_content = ""

            # Attachment seems to be in b-conditional-link
            if (bug_id_prefix == 'c'):
                scraped_content = self.__scrape_chromium_report(driver, bug_id, save_scraped_content)
            else:
                scraped_content = self.__scrape_bugzilla_report(driver, bug_id, save_scraped_content)

            # Close the browser
            driver.quit()
            return scraped_content

    def try_get_bug_report(self, bug_id):
        saved_result = self.__try_get_bug_existing_report(bug_id)
        if (saved_result):
            return saved_result
        else:
            return self.scrape_bug_report(bug_id)
    
    # Get expected bug report based on USE_URLS
    #   if true: return the url of a bugreport as only info
    #   if false: return scraped bug description
    def __try_get_bug_existing_report(self, bug_id):
        if (self.use_urls):
            report = self.__get_bug_report_link(bug_id)
        else:
            report = self.__get_scraped_bug_report(bug_id)
        return report
        
    # Get the scraped bug description for a given bug_id
    def __get_scraped_bug_report(self, bug_id):
        report_file = self.report_path(bug_id)
        if (os.path.exists(report_file)):
            with open(report_file, "r") as f:
                return f.read()
        else: 
            return ""

    # Get bug report link for a given bug_id
    # -- not to be used, as openAI API is not yet capable of visiting links --
    def __get_bug_report_link(self, bug_id):
        url = "Visit the following link, look for the bug report / description and follow and analyse all given steps (visit given links, when possible, too): "
        bug_id_no_prefix = bug_id[1:]
        bug_id_prefix = bug_id[0]
        if (bug_id_prefix == 'c'):
            url += f"https://bugs.chromium.org/p/chromium/issues/detail?id={bug_id_no_prefix}"
        else:
            url += f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug_id_no_prefix}"
        return url
    

    def __scrape_chromium_report(self, driver, bug_id, save_scraped_content = False):
        bug_id_no_prefix = bug_id[1:]

        url = f"https://bugs.chromium.org/p/chromium/issues/detail?id={bug_id_no_prefix}"
        driver.get(url)

        # Wait for JavaScript to load
        time.sleep(5)

        issue_description = driver.find_element(By.TAG_NAME, "b-issue-description")
        scraped_content = ""

        # Seems that there are two ways of adding a description either unformatted in div.child or formatted in div.type-m.markdown-display
        try:
            # try fetching div.child first
            scraped_content = issue_description.find_element(By.CSS_SELECTOR, "div.child").text
            if (save_scraped_content):
                self.__write_report_to_file(scraped_content, bug_id)

        # if element not found exception
        except NoSuchElementException:
            try:
                # try fetching div.type-m.markdown-display
                scraped_content = issue_description.find_element(By.CSS_SELECTOR, "div.type-m.markdown-display").text
                if (save_scraped_content):
                    self.__write_report_to_file(scraped_content, bug_id)
                    
            except Exception as e:
                print(f"div.type-m.markdown-display did also not work for: {bug_id}")
            
        except Exception as e:
            print(f"Something other than NoSuchElement went wrong for: {bug_id}")
        
        try:
            links = issue_description.find_elements(By.CSS_SELECTOR, 'a.normal-link.ng-star-inserted')
            hrefs = [link.get_attribute("href") for link in links if link.text == "View"]

            div_attachment_names = issue_description.find_elements(By.CSS_SELECTOR, 'div.bv2-issue-attachment-filename')
            attachment_names = [div_attachment_name.text for div_attachment_name in div_attachment_names]
            print(attachment_names)

            for i in range(len(hrefs)):
                attachment_name = attachment_names[i]

                if (os.path.splitext(attachment_name)[1] in allowed_extensions):
                    driver.get(hrefs[i]) # type: ignore
                    time.sleep(5)

                    plain_text = driver.find_element(By.TAG_NAME, "body").text

                    if (save_scraped_content):
                        self.__write_report_to_file(f"\nWith attachment: {attachment_name}\n" + plain_text + "\n", bug_id, "a")
                    else:
                        scraped_content += f"\nWith attachment: {attachment_name}\n" + plain_text + "\n"

        except Exception as e:
            print(f"Something went wrong trying to scrape file for bug {bug_id}, error: {e}")
        
        return scraped_content

    

    def __scrape_bugzilla_report(self, driver, bug_id, save_scraped_content = False):
        bug_id_no_prefix = bug_id[1:]
        url = f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug_id_no_prefix}"
        driver.get(url)

        # Wait for JavaScript to load
        time.sleep(5)

        try:
            # Find the <div> by ID
            div_content = driver.find_element(By.CSS_SELECTOR, "div#c0")
            scraped_content = div_content.find_element(By.ID, "ct-0").text

            if (save_scraped_content):
                self.__write_report_to_file(scraped_content, bug_id)
            
            try:
                attachment_section = driver.find_element(By.CSS_SELECTOR, "section#module-attachments")
                attachement_divs = attachment_section.find_elements(By.CSS_SELECTOR, "div.attach-desc")

                for attachement_div in attachement_divs:
                    link = attachement_div.find_element(By.TAG_NAME, "a")
                    href = link.get_attribute("href") + "&action=edit"
                    #href = f"https://bugzilla.mozilla.org{href_postfix}&action=edit"
                    print(href)
                    attachment_name = link.text

                    if (os.path.splitext(attachment_name)[1] in allowed_extensions):
                        driver.get(href) # type: ignore
                        time.sleep(5)

                        plain_text = driver.find_element(By.ID, "viewFrame").text
                        print(plain_text)

                        if (save_scraped_content):
                            self.__write_report_to_file(f"\nWith attachment: {attachment_name}\n" + plain_text + "\n", bug_id, "a")
                        else:
                            scraped_content += f"\nWith attachment: {attachment_name}\n" + plain_text + "\n"
                        driver.back()
                        time.sleep(2)

            except Exception as e:
                print(f"Error processing div: {e}")
            
            return scraped_content

        except Exception as e:
            print(f"Error extracting content for bug: {bug_id}")


    def __write_report_to_file(self, content, bug_id, mode = "w"):
        # If succesful, save scraped content to report file
        with open(f"{self.report_path(bug_id)}", mode, encoding="utf-8") as f:
            f.write(content)
            print(f"wrote for bug {bug_id}")