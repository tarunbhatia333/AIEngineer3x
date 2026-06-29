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

public class TC_002_SuccessfulOTPLogin {

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {
        // TODO: Set the path to chromedriver executable if not using WebDriverManager
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--start-maximized");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(priority = 2)
    public void successfulOtpLoginWithRegisteredMobileNumber() {
        // 1. Open the login page
        // TODO: Replace with the actual base URL of the application
        driver.get("TODO_BASE_URL/login");

        // 2. Enter a valid registered mobile number in the input field
        // TODO: Replace By.id("mobileInput") with the actual locator for the mobile number field
        By mobileInputLocator = By.id("mobileInput");
        WebElement mobileInput = wait.until(ExpectedConditions.visibilityOfElementLocated(mobileInputLocator));
        mobileInput.clear();
        // TODO: Replace with a valid registered mobile number for the test environment
        mobileInput.sendKeys("TODO_REGISTERED_MOBILE_NUMBER");

        // 3. Click the "Request OTP" button
        // TODO: Replace By.id("requestOtpBtn") with the actual locator for the Request OTP button
        By requestOtpBtnLocator = By.id("requestOtpBtn");
        WebElement requestOtpBtn = wait.until(ExpectedConditions.elementToBeClickable(requestOtpBtnLocator));
        requestOtpBtn.click();

        // 4. Receive OTP via SMS (mocked)
        // In a real test, retrieve the OTP from a service or database.
        // For now, we mock the OTP value.
        // TODO: Replace "123456" with the mechanism to fetch the actual OTP.
        String otpCode = "123456";

        // 5. Enter the correct 6‑digit OTP
        // TODO: Replace By.id("otpInput") with the actual locator for the OTP input field
        By otpInputLocator = By.id("otpInput");
        WebElement otpInput = wait.until(ExpectedConditions.visibilityOfElementLocated(otpInputLocator));
        otpInput.clear();
        otpInput.sendKeys(otpCode);

        // 6. Click the "Proceed" button
        // TODO: Replace By.id("proceedBtn") with the actual locator for the Proceed button
        By proceedBtnLocator = By.id("proceedBtn");
        WebElement proceedBtn = wait.until(ExpectedConditions.elementToBeClickable(proceedBtnLocator));
        proceedBtn.click();

        // Expected Result: User is authenticated and redirected to their account dashboard
        // Wait for an element that uniquely identifies the dashboard page.
        // TODO: Replace By.id("dashboardHeader") with a reliable locator present only on the dashboard.
        By dashboardHeaderLocator = By.id("dashboardHeader");
        WebElement dashboardHeader = wait.until(ExpectedConditions.visibilityOfElementLocated(dashboardHeaderLocator));

        // Assertion to confirm successful navigation
        Assert.assertTrue(dashboardHeader.isDisplayed(),
                "Dashboard header should be displayed after successful OTP login.");

        // Optional: Verify URL contains expected path
        // TODO: Adjust the expected URL fragment if different.
        String currentUrl = driver.getCurrentUrl();
        Assert.assertTrue(currentUrl.contains("/dashboard"),
                "Current URL should contain '/dashboard' after successful login.");
    }
}