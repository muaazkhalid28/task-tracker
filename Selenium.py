"""
Selenium test for the Task Tracker app (login + dashboard).

Usage:
    python test_app.py http://YOUR-ALB-DNS-NAME
    python test_app.py http://YOUR-EC2-PUBLIC-IP
    python test_app.py http://YOUR-ALB-DNS-NAME --headless     (no browser window)

The URL is passed as an argument, so nothing is hard-coded to localhost.
"""
import sys
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

parser = argparse.ArgumentParser()
parser.add_argument("url", help="Base URL, e.g. http://my-alb-123.us-east-1.elb.amazonaws.com")
parser.add_argument("--headless", action="store_true", help="Run without opening a browser window")
args = parser.parse_args()

URL = args.url.rstrip("/")
if not URL.startswith("http"):
    URL = "http://" + URL

options = Options()
if args.headless:
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)
passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"PASSED: {name}")
    else:
        failed += 1
        print(f"FAILED: {name}")


try:
    print(f"Testing application at: {URL}\n")

    # Test 1: open the application and verify the login page element
    driver.get(URL)
    heading = wait.until(EC.visibility_of_element_located((By.ID, "login-title")))
    check("Login page opens and heading is visible", "Login" in heading.text)
    print("   Heading text:", heading.text)
    driver.save_screenshot("selenium_1_login_page.png")

    # Test 2: wrong password shows an error message
    driver.find_element(By.ID, "username-input").send_keys("admin")
    driver.find_element(By.ID, "password-input").send_keys("wrongpass")
    driver.find_element(By.ID, "login-btn").click()
    error = wait.until(EC.visibility_of_element_located((By.ID, "error")))
    check("Wrong password is rejected", "Wrong username or password" in error.text)

    # Test 3: correct login opens the dashboard
    user_box = driver.find_element(By.ID, "username-input")
    user_box.clear()
    user_box.send_keys("admin")
    pass_box = driver.find_element(By.ID, "password-input")
    pass_box.clear()
    pass_box.send_keys("admin123")
    driver.find_element(By.ID, "login-btn").click()
    welcome = wait.until(EC.visibility_of_element_located((By.ID, "welcome")))
    check("Login works and dashboard opens", "Welcome, admin" in welcome.text)
    print("   Served by container:", driver.find_element(By.ID, "host").text)
    driver.save_screenshot("selenium_2_dashboard.png")

    # Test 4: add a task and verify it appears in the list
    task_name = "Selenium task " + str(int(time.time()))
    driver.find_element(By.ID, "task-input").send_keys(task_name)
    driver.find_element(By.ID, "add-btn").click()
    try:
        wait.until(EC.text_to_be_present_in_element((By.ID, "task-list"), task_name))
        added = True
    except Exception:
        added = False
    check("New task appears in the task list", added)
    driver.save_screenshot("selenium_3_task_added.png")

    # Test 5: logout returns to the login page
    driver.find_element(By.ID, "logout-link").click()
    heading = wait.until(EC.visibility_of_element_located((By.ID, "login-title")))
    check("Logout returns to the login page", "Login" in heading.text)

    # Test 6: dashboard is protected after logout
    driver.get(URL + "/dashboard")
    wait.until(EC.visibility_of_element_located((By.ID, "login-title")))
    check("Dashboard is protected (redirects to login)", "/login" in driver.current_url)

finally:
    driver.quit()

print(f"\nResults: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)