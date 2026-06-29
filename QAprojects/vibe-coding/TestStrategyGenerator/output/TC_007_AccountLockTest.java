package com.example.tests;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.*;

import java.time.Duration;

public class TC_007_AccountLockTest {

    private WebDriver driver;
    private WebDriverWait wait;

    // TODO: Replace with the actual base URL of the application under test
    private static final String BASE_URL = "TODO_BASE_URL";

    @BeforeMethod
    public void setUp() {
        // TODO: If using WebDriverManager, add the dependency and initialize here.
        // Example: WebDriverManager.chromedriver().setup();
        driver = new ChromeDriver();
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test
    public void testAccountLockAfterFailedAttempts() {
        // Step 1 – Open the login page
        driver.get(BASE_URL + "/TODO_LOGIN_PATH");

        // TODO: Define the actual locators for the elements on the login page
        By identifierField = By.id("TODO_IDENTIFIER_FIELD_ID");
        By proceedButton   = By.id("TODO_PROCEED_BUTTON_ID");
        By passwordField   = By.id("TODO_PASSWORD_FIELD_ID");
        By loginButton     = By.id("TODO_LOGIN_BUTTON_ID");
        By lockoutMessage  = By.id("TODO_LOCKOUT_MESSAGE_ID");

        // TODO: Populate with real test data
        String registeredIdentifier = "TODO_REGISTERED_IDENTIFIER";
        String incorrectPassword    = "TODO_INCORRECT_PASSWORD";
        String correctPassword      = "TODO_CORRECT_PASSWORD";

        // Perform five consecutive failed login attempts
        for (int attempt = 1; attempt <= 5; attempt++) {
            // Enter the registered identifier (email or mobile)
            WebElement idElem = wait.until(ExpectedConditions.visibilityOfElementLocated(identifierField));
            idElem.clear();
            idElem.sendKeys(registeredIdentifier);

            // Click "Proceed"
            wait.until(ExpectedConditions.elementToBeClickable(proceedButton)).click();

            // Enter an incorrect password or OTP
            WebElement pwdElem = wait.until(ExpectedConditions.visibilityOfElementLocated(passwordField));
            pwdElem.clear();
            pwdElem.sendKeys(incorrectPassword);

            // Submit the login form
            wait.until(ExpectedConditions.elementToBeClickable(loginButton)).click();

            // Optional: Verify a generic authentication failure message
            // TODO: Add verification of the failure message if required

            // Optional: Ensure we are back on the login page for the next iteration
            // TODO: Add navigation back to the login page if the application does not do it automatically
        }

        // Sixth attempt – use correct credentials
        WebElement idElem = wait.until(ExpectedConditions.visibilityOfElementLocated(identifierField));
        idElem.clear();
        idElem.sendKeys(registeredIdentifier);
        wait.until(ExpectedConditions.elementToBeClickable(proceedButton)).click();

        WebElement pwdElem = wait.until(ExpectedConditions.visibilityOfElementLocated(passwordField));
        pwdElem.clear();
        pwdElem.sendKeys(correctPassword);
        wait.until(ExpectedConditions.elementToBeClickable(loginButton)).click();

        // Verify that the account lockout message is displayed
        WebElement lockoutElem = wait.until(ExpectedConditions.visibilityOfElementLocated(lockoutMessage));
        Assert.assertTrue(lockoutElem.isDisplayed(),
                "Lockout message should be displayed after the account is locked.");
    }
}