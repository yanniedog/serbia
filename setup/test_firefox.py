from selenium import webdriver

driver = webdriver.Firefox()
driver.get("https://www.google.com")
print(driver.title)
driver.quit()
