package com.flipkart.tests;

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

public class TC_001_VerifyLoginPageUIElementsAndBranding {

    private WebDriver driver;
    private WebDriverWait wait;

    // TODO: Set the path to your ChromeDriver executable
    private static final String CHROME_DRIVER_PATH = "TODO_PATH_TO_CHROMEDRIVER";

    // TODO: Set the base URL for Flipkart
    private static final String BASE_URL = "TODO_BASE_URL";

    // Locators – replace the placeholder XPATH/CSS with actual values when available
    private static final By LOGIN_LINK = By.xpath("TODO_LOGIN_LINK_XPATH");
    private static final By BRANDING_ELEMENT = By.xpath("TODO_BRANDING_ELEMENT_XPATH");
    private static final By EMAIL_MOBILE_INPUT = By.xpath("TODO_EMAIL_MOBILE_INPUT_XPATH");
    private static final By PROCEED_BUTTON = By.xpath("TODO_PROCEED_BUTTON_XPATH");
    private static final By REQUEST_OTP_BUTTON = By.xpath("TODO_REQUEST_OTP_BUTTON_XPATH");
    private static final By TERMS_OF_USE_LINK = By.xpath("TODO_TERMS_OF_USE_LINK_XPATH");
    private static final By PRIVACY_POLICY_LINK = By.xpath("TODO_PRIVACY_POLICY_LINK_XPATH");

    @BeforeMethod
    public void setUp() {
        System.setProperty("webdriver.chrome.driver", CHROME_DRIVER_PATH);
        ChromeOptions options = new ChromeOptions();
        // Add any required Chrome options here
        driver = new ChromeDriver(options);
        driver.manage().window().maximize();

        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
        driver.get(BASE_URL);
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test(description = "TC-001: Verify Login Page UI Elements and Branding", priority = 2)
    public void verifyLoginPageUIElementsAndBranding() {
        // Step 1: Click the login link to open the login modal/page
        WebElement loginLink = wait.until(ExpectedConditions.elementToBeClickable(LOGIN_LINK));
        loginLink.click();

        // Step 2: Observe the displayed branding elements
        WebElement branding = wait.until(ExpectedConditions.visibilityOfElementLocated(BRANDING_ELEMENT));
        Assert.assertTrue(branding.isDisplayed(), "Branding element should be displayed.");

        // Step 3: Verify presence of a single input field for Email/Mobile
        WebElement emailMobileInput = wait.until(ExpectedConditions.visibilityOfElementLocated(EMAIL_MOBILE_INPUT));
        Assert.assertTrue(emailMobileInput.isDisplayed(), "Email/Mobile input field should be displayed.");

        // Step 4: Verify presence of \"Proceed\" button
        WebElement proceedBtn = wait.until(ExpectedConditions.visibilityOfElementLocated(PROCEED_BUTTON));
        Assert.assertTrue(proceedBtn.isDisplayed(), "\"Proceed\" button should be displayed.");

        // Step 5: Verify presence of \"Request OTP\" button
        WebElement requestOtpBtn = wait.until(ExpectedConditions.visibilityOfElementLocated(REQUEST_OTP_BUTTON));
        Assert.assertTrue(requestOtpBtn.isDisplayed(), "\"Request OTP\" button should be displayed.");

        // Step 6: Verify presence of \"Terms of Use\" and \"Privacy Policy\" links
        WebElement termsLink = wait.until(ExpectedConditions.visibilityOfElementLocated(TERMS_OF_USE_LINK));
        Assert.assertTrue(termsLink.isDisplayed(), "\"Terms of Use\" link should be displayed.");

        WebElement privacyLink = wait.until(ExpectedConditions.visibilityOfElementLocated(PRIVACY_POLICY_LINK));
        Assert.assertTrue(privacyLink.isDisplayed(), "\"Privacy Policy\" link should be displayed.");

        // Optional: Verify that the links are functional (click and verify navigation)
        // TODO: Add navigation verification if required
    }
}