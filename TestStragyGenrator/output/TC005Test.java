import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.time.Duration;

public class TC005Test {

    private WebDriver driver;
    private WebDriverWait wait;

    // TODO: Replace with the actual login page URL
    private static final String BASE_URL = "TODO: https://your-application-login-page.com";

    // TODO: Replace with actual locators
    private static final By EMAIL_FIELD = By.id("emailField"); // placeholder
    private static final By PROCEED_BUTTON = By.id("proceedButton"); // placeholder
    private static final By ERROR_MESSAGE = By.id("errorMessage"); // placeholder

    @BeforeMethod
    public void setUp() {
        // Set ChromeDriver path if not using WebDriverManager
        // System.setProperty("webdriver.chrome.driver", "/path/to/chromedriver");

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless"); // Remove if you want to see the browser
        driver = new ChromeDriver(options);
        driver.manage().window().maximize();

        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        driver.get(BASE_URL);
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(priority = 2, description = "Error Message for Blank Input Field")
    public void testBlankEmailFieldShowsErrorMessage() {
        // Step 1: Ensure the Email/Mobile input field is empty (do not send any keys)
        WebElement emailInput = wait.until(ExpectedConditions.visibilityOfElementLocated(EMAIL_FIELD));
        emailInput.clear();

        // Step 2: Click the "Proceed" button
        WebElement proceedBtn = wait.until(ExpectedConditions.elementToBeClickable(PROCEED_BUTTON));
        proceedBtn.click();

        // Expected Result: Verify error message is displayed with correct text
        WebElement errorMsgElement = wait.until(ExpectedConditions.visibilityOfElementLocated(ERROR_MESSAGE));
        String actualErrorMessage = errorMsgElement.getText().trim();
        String expectedErrorMessage = "Please enter your Email/Mobile number.";

        Assert.assertEquals(actualErrorMessage, expectedErrorMessage,
                "Error message text does not match the expected value.");
    }
}