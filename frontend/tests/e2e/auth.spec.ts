import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the home page before each test
    await page.goto('/');
  });

  test('should display login form on home page', async ({ page }) => {
    // Click the login button to open the modal
    await page.click('button:has-text("Login")');
    
    // Check if login form elements are present in the modal
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check for login form labels
    await expect(page.locator('text=Email')).toBeVisible();
    await expect(page.locator('text=Password')).toBeVisible();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    // Click the login button to open the modal
    await page.click('button:has-text("Login")');
    
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Check for validation messages
    await expect(page.locator('text=Email is required')).toBeVisible();
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('should show validation error for invalid email format', async ({ page }) => {
    // Click the login button to open the modal
    await page.click('button:has-text("Login")');
    
    // Enter invalid email
    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Check for email validation error
    await expect(page.locator('text=Please enter a valid email address')).toBeVisible();
  });

  test('should show error for non-existent user login', async ({ page }) => {
    // Click the login button to open the modal
    await page.click('button:has-text("Login")');
    
    // Enter credentials for non-existent user
    await page.fill('input[type="email"]', 'nonexistent@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    // Check for login error message
    await expect(page.locator('text=Invalid email or password')).toBeVisible();
  });

  test('should successfully register a new user', async ({ page }) => {
    // Click the login button to open the modal
    await page.click('button:has-text("Login")');
    
    // Navigate to registration if there's a link
    const registerLink = page.locator('text=Sign up').or(page.locator('text=Register'));
    if (await registerLink.isVisible()) {
      await registerLink.click();
    }
    
    // Fill registration form
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@example.com`;
    
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="confirmPassword"]', 'TestPassword123!');
    
    // Submit registration
    await page.click('button[type="submit"]');
    
    // Check for success message
    await expect(page.locator('text=Registration successful')).toBeVisible();
    
    // Should redirect to login or show success state
    await expect(page.locator('text=Please check your email for verification')).toBeVisible();
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Click the login button to open the modal
    await page.click('button:has-text("Login")');
    
    // First register a user
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@example.com`;
    
    // Register user (assuming registration endpoint works)
    await page.evaluate(async (email) => {
      const response = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      return response.ok;
    }, testEmail);
    
    // Now try to login
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    
    // Check for successful login
    await expect(page.locator('text=Login successful')).toBeVisible();
    
    // Should redirect to dashboard or show authenticated state
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('should show password reset form', async ({ page }) => {
    // Look for forgot password link
    const forgotPasswordLink = page.locator('text=Forgot password?').or(page.locator('text=Forgot Password'));
    
    if (await forgotPasswordLink.isVisible()) {
      await forgotPasswordLink.click();
      
      // Check if password reset form is shown
      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('text=Reset Password')).toBeVisible();
      
      // Test password reset form
      await page.fill('input[type="email"]', 'test@example.com');
      await page.click('button[type="submit"]');
      
      // Check for success message
      await expect(page.locator('text=Password reset email sent')).toBeVisible();
    }
  });

  test('should handle logout functionality', async ({ page }) => {
    // First login (assuming we have a test user)
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@example.com`;
    
    // Register and login
    await page.evaluate(async (email) => {
      await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      const loginResponse = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      if (loginResponse.ok) {
        const data = await loginResponse.json();
        localStorage.setItem('token', data.access_token);
      }
    }, testEmail);
    
    // Refresh page to load authenticated state
    await page.reload();
    
    // Look for logout button
    const logoutButton = page.locator('text=Logout').or(page.locator('button:has-text("Logout")'));
    
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      
      // Check if redirected to login page
      await expect(page.locator('input[type="email"]')).toBeVisible();
      await expect(page.locator('text=Logout successful')).toBeVisible();
    }
  });

  test('should persist login state across page refreshes', async ({ page }) => {
    // Login first
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@example.com`;
    
    await page.evaluate(async (email) => {
      await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      const loginResponse = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      if (loginResponse.ok) {
        const data = await loginResponse.json();
        localStorage.setItem('token', data.access_token);
      }
    }, testEmail);
    
    // Refresh page
    await page.reload();
    
    // Check if still logged in
    await expect(page.locator('text=Welcome')).toBeVisible();
    await expect(page.locator('input[type="email"]')).not.toBeVisible();
  });

  test('should show user profile information when logged in', async ({ page }) => {
    // Login first
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@example.com`;
    
    await page.evaluate(async (email) => {
      await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      const loginResponse = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      if (loginResponse.ok) {
        const data = await loginResponse.json();
        localStorage.setItem('token', data.access_token);
      }
    }, testEmail);
    
    await page.reload();
    
    // Look for user profile or dashboard
    const profileSection = page.locator('[data-testid="user-profile"]').or(page.locator('text=Profile'));
    
    if (await profileSection.isVisible()) {
      await profileSection.click();
      
      // Check if user email is displayed
      await expect(page.locator(`text=${testEmail}`)).toBeVisible();
    }
  });
});
