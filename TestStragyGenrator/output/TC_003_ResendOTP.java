package tests;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.*;

import java.time.Duration;

public class TC_003_ResendOTP {

    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeMethod
    public void setUp() {
        // TODO: Set the path to chromedriver if not using WebDriverManager
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--start-maximized");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(30));
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(priority = 2, description = "Resend OTP after Countdown Expiration")
    public void testResendOtpAfterCountdown() {
        // 1. Open the login page
        driver.get("TODO_BASE_URL/login"); // TODO: Replace with actual login page URL

        // 2. Enter a valid registered mobile number
        By mobileInputLocator = By.id("TODO_MOBILE_INPUT_ID"); // TODO: Replace with actual locator
        WebElement mobileInput = wait.until(ExpectedConditions.visibilityOfElementLocated(mobileInputLocator));
        mobileInput.clear();
        mobileInput.sendKeys("TODO_VALID_MOBILE_NUMBER"); // TODO: Replace with a valid test mobile number

        // 3. Click "Request OTP"
        By requestOtpButtonLocator = By.id("TODO_REQUEST_OTP_BUTTON_ID"); // TODO: Replace with actual locator
        WebElement requestOtpButton = wait.until(ExpectedConditions.elementToBeClickable(requestOtpButtonLocator));
        requestOtpButton.click();

        // 4. Wait for the 60‑second countdown to reach zero
        By countdownLocator = By.id("TODO_COUNTDOWN_TIMER_ID"); // TODO: Replace with actual locator
        // Assuming the timer displays seconds as plain text, e.g., "0"
        wait.until((WebDriver d) -> {
            String text = d.findElement(countdownLocator).getText().trim();
            return text.equals("0");
        });

        // 5. Click the "Resend OTP" link/button
        By resendOtpLocator = By.id("TODO_RESEND_OTP_LINK_ID"); // TODO: Replace with actual locator
        WebElement resendOtpLink = wait.until(ExpectedConditions.elementToBeClickable(resendOtpLocator));
        resendOtpLink.click();

        // Expected Result: A new OTP is sent and a fresh 60‑second timer starts
        // Verify that the countdown timer restarts (e.g., shows "60" or a non‑zero value)
        // We'll wait until the timer text becomes a non‑zero value and assert it's greater than zero.
        wait.until(ExpectedConditions.not(ExpectedConditions.textToBe(countdownLocator, "0")));
        String timerText = driver.findElement(countdownLocator).getText().trim();
        try {
            int timerValue = Integer.parseInt(timerText);
            Assert.assertTrue(timerValue > 0, "Timer should restart with a value greater than 0 after resending OTP.");
        } catch (NumberFormatException e) {
            Assert.fail("Countdown timer text is not a numeric value: " + timerText);
        }

        // Additional verification could include checking a toast/message that OTP was sent.
        // TODO: Add verification for OTP sent confirmation if applicable.
    }
}