package tests;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.time.Duration;

public class TC_006 {

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {
        // TODO: Set the path to the chromedriver executable if not using WebDriverManager
        // System.setProperty("webdriver.chrome.driver", "/path/to/chromedriver");
        driver = new ChromeDriver();
        driver.manage().window().maximize();

        // Initialize explicit wait
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        // TODO: Replace with the actual base URL of the login page
        String baseUrl = "TODO_BASE_URL";
        driver.get(baseUrl);
    }

    @Test
    public void verifyInvalidEmailErrorMessage() {
        // TODO: Replace with the actual locator for the email input field
        By emailInputLocator = By.id("TODO_EMAIL_INPUT_ID");

        // TODO: Replace with the actual locator for the "Proceed" button
        By proceedButtonLocator = By.id("TODO_PROCEED_BUTTON_ID");

        // TODO: Replace with the actual locator for the error message element
        By errorMessageLocator = By.id("TODO_ERROR_MESSAGE_ID");

        // Step 1: Enter an incorrectly formatted email
        WebElement emailInput = wait.until(ExpectedConditions.visibilityOfElementLocated(emailInputLocator));
        emailInput.clear();
        emailInput.sendKeys("userexample.com"); // missing '@'

        // Step 2: Click the "Proceed" button
        WebElement proceedButton = wait.until(ExpectedConditions.elementToBeClickable(proceedButtonLocator));
        proceedButton.click();

        // Expected Result: Verify error message is displayed
        WebElement errorMessageElement = wait.until(ExpectedConditions.visibilityOfElementLocated(errorMessageLocator));
        String actualErrorMessage = errorMessageElement.getText().trim();

        String expectedErrorMessage = "Please enter a valid Email address.";
        Assert.assertEquals(actualErrorMessage, expectedErrorMessage,
                "Error message for invalid email format does not match expected.");
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}