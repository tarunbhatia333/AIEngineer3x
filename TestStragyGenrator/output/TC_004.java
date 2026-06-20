package tests;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.*;

import java.time.Duration;

public class TC_004 {

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {
        // TODO: Set the path to chromedriver if not using WebDriverManager
        // System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        driver = new ChromeDriver();
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(priority = 2, description = "Successful Password Login with Registered Email")
    public void successfulPasswordLoginWithRegisteredEmail() {
        // 1. Open the login page
        driver.get("TODO_BASE_URL/login"); // TODO: Replace with actual base URL

        // 2. Enter a valid registered email address in the input field
        By emailInputLocator = By.id("TODO_EMAIL_INPUT_ID"); // TODO: Replace with actual locator
        WebElement emailInput = wait.until(ExpectedConditions.visibilityOfElementLocated(emailInputLocator));
        emailInput.clear();
        emailInput.sendKeys("registered_user@example.com"); // TODO: Replace with a valid test email

        // 3. Click the "Proceed" button
        By proceedButtonAfterEmailLocator = By.id("TODO_PROCEED_BUTTON_AFTER_EMAIL_ID"); // TODO: Replace with actual locator
        WebElement proceedAfterEmailBtn = wait.until(ExpectedConditions.elementToBeClickable(proceedButtonAfterEmailLocator));
        proceedAfterEmailBtn.click();

        // 4. Enter the correct password in the password field
        By passwordInputLocator = By.id("TODO_PASSWORD_INPUT_ID"); // TODO: Replace with actual locator
        WebElement passwordInput = wait.until(ExpectedConditions.visibilityOfElementLocated(passwordInputLocator));
        passwordInput.clear();
        passwordInput.sendKeys("CorrectPassword123"); // TODO: Replace with a valid test password

        // 5. Click the "Proceed" button again
        By proceedButtonAfterPasswordLocator = By.id("TODO_PROCEED_BUTTON_AFTER_PASSWORD_ID"); // TODO: Replace with actual locator
        WebElement proceedAfterPasswordBtn = wait.until(ExpectedConditions.elementToBeClickable(proceedButtonAfterPasswordLocator));
        proceedAfterPasswordBtn.click();

        // Expected Result: User is authenticated and redirected to their account dashboard
        // Verify that the dashboard page is displayed
        By dashboardHeaderLocator = By.id("TODO_DASHBOARD_HEADER_ID"); // TODO: Replace with an element unique to the dashboard
        WebElement dashboardHeader = wait.until(ExpectedConditions.visibilityOfElementLocated(dashboardHeaderLocator));
        Assert.assertTrue(dashboardHeader.isDisplayed(), "Dashboard header should be displayed, indicating successful login.");
    }
}