package tests;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.*;

import java.time.Duration;

public class TC_008_ShowHidePasswordToggleTest {

    private WebDriver driver;
    private WebDriverWait wait;
    // TODO: Replace with the actual base URL of the application under test
    private static final String BASE_URL = "TODO_BASE_URL";

    @BeforeMethod
    public void setUp() {
        ChromeOptions options = new ChromeOptions();
        // Add any required Chrome options here
        driver = new ChromeDriver(options);
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(priority = 2, description = "TC-008: Show/Hide Password Toggle Functionality")
    public void testShowHidePasswordToggle() {
        // 1. Navigate to the login view (precondition)
        driver.get(BASE_URL + "/TODO_LOGIN_PATH"); // TODO: Append correct path to reach the password login view

        // 2. Enter a registered email and click "Proceed"
        // TODO: Replace selectors with actual identifiers
        By emailFieldLocator = By.id("email"); // TODO
        By proceedButtonLocator = By.id("proceedBtn"); // TODO

        WebElement emailField = wait.until(ExpectedConditions.visibilityOfElementLocated(emailFieldLocator));
        emailField.clear();
        emailField.sendKeys("registered_user@example.com"); // TODO: Use a valid test email

        WebElement proceedButton = wait.until(ExpectedConditions.elementToBeClickable(proceedButtonLocator));
        proceedButton.click();

        // 3. Observe the password input field with a "Show" icon
        // TODO: Replace selectors with actual identifiers
        By passwordFieldLocator = By.id("password"); // TODO
        By toggleIconLocator = By.id("togglePassword"); // TODO

        WebElement passwordField = wait.until(ExpectedConditions.visibilityOfElementLocated(passwordFieldLocator));
        WebElement toggleIcon = wait.until(ExpectedConditions.elementToBeClickable(toggleIconLocator));

        // Verify that the password field is initially masked
        String initialType = passwordField.getAttribute("type");
        Assert.assertEquals(initialType, "password", "Password field should be masked initially.");

        // 4. Click the "Show" icon
        toggleIcon.click();

        // 5. Verify the password characters are displayed in plain text
        // Wait for the type attribute to change to "text"
        wait.until(ExpectedConditions.attributeToBe(passwordFieldLocator, "type", "text"));
        String afterShowType = passwordField.getAttribute("type");
        Assert.assertEquals(afterShowType, "text", "Password field should be displayed in plain text after clicking Show.");

        // 6. Click the "Hide" icon (the same toggle element)
        toggleIcon.click();

        // 7. Verify the password characters are masked again
        wait.until(ExpectedConditions.attributeToBe(passwordFieldLocator, "type", "password"));
        String afterHideType = passwordField.getAttribute("type");
        Assert.assertEquals(afterHideType, "password", "Password field should be masked again after clicking Hide.");
    }
}