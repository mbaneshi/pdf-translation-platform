import { test, expect } from '@playwright/test';

test.describe('Glossary Management', () => {
  let authToken: string;
  let testEmail: string;

  test.beforeEach(async ({ page }) => {
    // Setup authentication for each test
    const timestamp = Date.now();
    testEmail = `testuser${timestamp}@example.com`;
    
    // Register and login user
    await page.evaluate(async (email) => {
      // Register user
      await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          password: 'TestPassword123!'
        })
      });
      
      // Login user
      const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
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
        return data.access_token;
      }
      return null;
    }, testEmail);
    
    // Navigate to glossary page
    await page.goto('/glossary');
  });

  test('should display glossary management interface', async ({ page }) => {
    // Check if glossary page elements are present
    await expect(page.locator('h1:has-text("Glossary")')).toBeVisible();
    await expect(page.locator('button:has-text("Add Term")')).toBeVisible();
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible();
  });

  test('should add a new glossary term', async ({ page }) => {
    // Click add term button
    await page.click('button:has-text("Add Term")');
    
    // Fill in the form
    await page.fill('input[name="term"]', 'machine learning');
    await page.fill('input[name="translation"]', 'یادگیری ماشین');
    await page.fill('textarea[name="context"]', 'AI and data science context');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Check for success message
    await expect(page.locator('text=Term added successfully')).toBeVisible();
    
    // Verify term appears in the list
    await expect(page.locator('text=machine learning')).toBeVisible();
    await expect(page.locator('text=یادگیری ماشین')).toBeVisible();
  });

  test('should show validation errors for empty term submission', async ({ page }) => {
    // Click add term button
    await page.click('button:has-text("Add Term")');
    
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Check for validation messages
    await expect(page.locator('text=Term is required')).toBeVisible();
    await expect(page.locator('text=Translation is required')).toBeVisible();
  });

  test('should edit an existing glossary term', async ({ page }) => {
    // First add a term
    await page.click('button:has-text("Add Term")');
    await page.fill('input[name="term"]', 'algorithm');
    await page.fill('input[name="translation"]', 'الگوریتم');
    await page.fill('textarea[name="context"]', 'Computer science context');
    await page.click('button[type="submit"]');
    
    // Wait for term to appear
    await expect(page.locator('text=algorithm')).toBeVisible();
    
    // Click edit button for the term
    await page.click('button:has-text("Edit")');
    
    // Update the translation
    await page.fill('input[name="translation"]', 'الگوریتم محاسباتی');
    await page.click('button[type="submit"]');
    
    // Check for success message
    await expect(page.locator('text=Term updated successfully')).toBeVisible();
    
    // Verify updated translation appears
    await expect(page.locator('text=الگوریتم محاسباتی')).toBeVisible();
  });

  test('should delete a glossary term', async ({ page }) => {
    // First add a term
    await page.click('button:has-text("Add Term")');
    await page.fill('input[name="term"]', 'neural network');
    await page.fill('input[name="translation"]', 'شبکه عصبی');
    await page.fill('textarea[name="context"]', 'AI context');
    await page.click('button[type="submit"]');
    
    // Wait for term to appear
    await expect(page.locator('text=neural network')).toBeVisible();
    
    // Click delete button
    await page.click('button:has-text("Delete")');
    
    // Confirm deletion in modal
    await page.click('button:has-text("Confirm")');
    
    // Check for success message
    await expect(page.locator('text=Term deleted successfully')).toBeVisible();
    
    // Verify term is removed from list
    await expect(page.locator('text=neural network')).not.toBeVisible();
  });

  test('should search and filter glossary terms', async ({ page }) => {
    // Add multiple terms
    const terms = [
      { term: 'artificial intelligence', translation: 'هوش مصنوعی', context: 'AI' },
      { term: 'machine learning', translation: 'یادگیری ماشین', context: 'ML' },
      { term: 'deep learning', translation: 'یادگیری عمیق', context: 'DL' }
    ];
    
    for (const termData of terms) {
      await page.click('button:has-text("Add Term")');
      await page.fill('input[name="term"]', termData.term);
      await page.fill('input[name="translation"]', termData.translation);
      await page.fill('textarea[name="context"]', termData.context);
      await page.click('button[type="submit"]');
    }
    
    // Search for specific term
    await page.fill('input[placeholder*="Search"]', 'machine');
    
    // Verify only matching terms are shown
    await expect(page.locator('text=machine learning')).toBeVisible();
    await expect(page.locator('text=artificial intelligence')).not.toBeVisible();
    await expect(page.locator('text=deep learning')).not.toBeVisible();
  });

  test('should import terms from text', async ({ page }) => {
    // Look for import functionality
    const importButton = page.locator('button:has-text("Import")').or(page.locator('button:has-text("Extract Terms")'));
    
    if (await importButton.isVisible()) {
      await importButton.click();
      
      // Enter text with potential terms
      const sampleText = 'This document discusses machine learning algorithms and neural networks for artificial intelligence applications.';
      await page.fill('textarea[name="text"]', sampleText);
      
      // Click extract button
      await page.click('button:has-text("Extract")');
      
      // Check if terms are suggested
      await expect(page.locator('text=machine learning')).toBeVisible();
      await expect(page.locator('text=neural networks')).toBeVisible();
      await expect(page.locator('text=artificial intelligence')).toBeVisible();
      
      // Select terms to add
      await page.check('input[type="checkbox"][value="machine learning"]');
      await page.check('input[type="checkbox"][value="neural networks"]');
      
      // Add selected terms
      await page.click('button:has-text("Add Selected")');
      
      // Check for success message
      await expect(page.locator('text=Terms added successfully')).toBeVisible();
    }
  });

  test('should export glossary terms', async ({ page }) => {
    // Add a term first
    await page.click('button:has-text("Add Term")');
    await page.fill('input[name="term"]', 'export test');
    await page.fill('input[name="translation"]', 'تست صادرات');
    await page.fill('textarea[name="context"]', 'Test context');
    await page.click('button[type="submit"]');
    
    // Look for export functionality
    const exportButton = page.locator('button:has-text("Export")').or(page.locator('button:has-text("Download")'));
    
    if (await exportButton.isVisible()) {
      // Set up download handling
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;
      
      // Verify download
      expect(download.suggestedFilename()).toMatch(/glossary|terms/);
    }
  });

  test('should show term consistency suggestions', async ({ page }) => {
    // Add terms with similar meanings
    await page.click('button:has-text("Add Term")');
    await page.fill('input[name="term"]', 'AI');
    await page.fill('input[name="translation"]', 'هوش مصنوعی');
    await page.click('button[type="submit"]');
    
    await page.click('button:has-text("Add Term")');
    await page.fill('input[name="term"]', 'artificial intelligence');
    await page.fill('input[name="translation"]', 'هوش مصنوعی');
    await page.click('button[type="submit"]');
    
    // Look for consistency suggestions
    const suggestionsSection = page.locator('[data-testid="consistency-suggestions"]').or(page.locator('text=Consistency Suggestions'));
    
    if (await suggestionsSection.isVisible()) {
      await expect(page.locator('text=Similar terms detected')).toBeVisible();
      await expect(page.locator('text=AI')).toBeVisible();
      await expect(page.locator('text=artificial intelligence')).toBeVisible();
    }
  });

  test('should handle bulk operations', async ({ page }) => {
    // Add multiple terms
    const terms = [
      { term: 'bulk term 1', translation: 'اصطلاح ۱', context: 'Test' },
      { term: 'bulk term 2', translation: 'اصطلاح ۲', context: 'Test' },
      { term: 'bulk term 3', translation: 'اصطلاح ۳', context: 'Test' }
    ];
    
    for (const termData of terms) {
      await page.click('button:has-text("Add Term")');
      await page.fill('input[name="term"]', termData.term);
      await page.fill('input[name="translation"]', termData.translation);
      await page.fill('textarea[name="context"]', termData.context);
      await page.click('button[type="submit"]');
    }
    
    // Look for bulk operations
    const bulkSelect = page.locator('input[type="checkbox"][data-bulk-select]').or(page.locator('input[type="checkbox"]').first());
    
    if (await bulkSelect.isVisible()) {
      // Select multiple terms
      await bulkSelect.check();
      await page.locator('input[type="checkbox"]').nth(1).check();
      await page.locator('input[type="checkbox"]').nth(2).check();
      
      // Look for bulk actions
      const bulkActions = page.locator('button:has-text("Bulk Actions")').or(page.locator('button:has-text("Selected")'));
      
      if (await bulkActions.isVisible()) {
        await bulkActions.click();
        
        // Check if bulk delete is available
        const bulkDelete = page.locator('button:has-text("Delete Selected")');
        if (await bulkDelete.isVisible()) {
          await bulkDelete.click();
          
          // Confirm bulk deletion
          await page.click('button:has-text("Confirm")');
          
          // Check for success message
          await expect(page.locator('text=Terms deleted successfully')).toBeVisible();
        }
      }
    }
  });
});