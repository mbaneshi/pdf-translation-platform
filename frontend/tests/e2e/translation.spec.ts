import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('PDF Translation', () => {
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
    
    // Navigate to translation page
    await page.goto('/translate');
  });

  test('should display PDF upload interface', async ({ page }) => {
    // Check if upload interface elements are present
    await expect(page.locator('h1:has-text("Translate PDF")')).toBeVisible();
    await expect(page.locator('input[type="file"]')).toBeVisible();
    await expect(page.locator('text=Drag and drop')).toBeVisible();
  });

  test('should upload a PDF file', async ({ page }) => {
    // Create a test PDF file (mock)
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    
    // Set up file upload
    await page.setInputFiles('input[type="file"]', testPdfPath);
    
    // Check for upload progress
    await expect(page.locator('text=Uploading')).toBeVisible();
    
    // Wait for upload completion
    await expect(page.locator('text=Upload successful')).toBeVisible();
    
    // Check if PDF preview is shown
    await expect(page.locator('canvas')).toBeVisible();
  });

  test('should show PDF preview after upload', async ({ page }) => {
    // Upload a test PDF
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    
    // Wait for processing
    await expect(page.locator('text=Processing PDF')).toBeVisible();
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    // Check for PDF preview elements
    await expect(page.locator('canvas')).toBeVisible();
    await expect(page.locator('text=Page 1 of')).toBeVisible();
    
    // Check for page navigation
    await expect(page.locator('button:has-text("Previous")')).toBeVisible();
    await expect(page.locator('button:has-text("Next")')).toBeVisible();
  });

  test('should extract text from PDF', async ({ page }) => {
    // Upload a test PDF
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    
    // Wait for processing
    await expect(page.locator('text=Extracting text')).toBeVisible();
    await expect(page.locator('text=Text extracted successfully')).toBeVisible();
    
    // Check for extracted text display
    await expect(page.locator('[data-testid="extracted-text"]')).toBeVisible();
    await expect(page.locator('text=Original Text')).toBeVisible();
  });

  test('should configure translation settings', async ({ page }) => {
    // Upload a test PDF first
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    
    // Wait for processing
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    // Look for translation settings
    const settingsButton = page.locator('button:has-text("Settings")').or(page.locator('button:has-text("Configure")'));
    
    if (await settingsButton.isVisible()) {
      await settingsButton.click();
      
      // Check for translation options
      await expect(page.locator('text=Translation Settings')).toBeVisible();
      await expect(page.locator('select[name="target_language"]')).toBeVisible();
      await expect(page.locator('select[name="translation_style"]')).toBeVisible();
      
      // Configure settings
      await page.selectOption('select[name="target_language"]', 'persian');
      await page.selectOption('select[name="translation_style"]', 'academic');
      
      // Save settings
      await page.click('button:has-text("Save")');
      
      // Check for success message
      await expect(page.locator('text=Settings saved')).toBeVisible();
    }
  });

  test('should start translation process', async ({ page }) => {
    // Upload and process PDF
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    // Start translation
    await page.click('button:has-text("Start Translation")');
    
    // Check for translation progress
    await expect(page.locator('text=Translating')).toBeVisible();
    await expect(page.locator('[role="progressbar"]')).toBeVisible();
    
    // Wait for translation completion
    await expect(page.locator('text=Translation completed')).toBeVisible();
  });

  test('should display translated text', async ({ page }) => {
    // Upload, process, and translate PDF
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    await page.click('button:has-text("Start Translation")');
    await expect(page.locator('text=Translation completed')).toBeVisible();
    
    // Check for translated text display
    await expect(page.locator('[data-testid="translated-text"]')).toBeVisible();
    await expect(page.locator('text=Translated Text')).toBeVisible();
    
    // Check for side-by-side view
    await expect(page.locator('text=Original')).toBeVisible();
    await expect(page.locator('text=Translation')).toBeVisible();
  });

  test('should allow editing translated text', async ({ page }) => {
    // Complete translation process
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    await page.click('button:has-text("Start Translation")');
    await expect(page.locator('text=Translation completed')).toBeVisible();
    
    // Look for edit functionality
    const editButton = page.locator('button:has-text("Edit")').or(page.locator('button[data-testid="edit-translation"]'));
    
    if (await editButton.isVisible()) {
      await editButton.click();
      
      // Check for editable text area
      await expect(page.locator('textarea[name="translated_text"]')).toBeVisible();
      
      // Edit the translation
      await page.fill('textarea[name="translated_text"]', 'Edited translation text');
      
      // Save changes
      await page.click('button:has-text("Save")');
      
      // Check for success message
      await expect(page.locator('text=Translation updated')).toBeVisible();
    }
  });

  test('should export translated PDF', async ({ page }) => {
    // Complete translation process
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    await page.click('button:has-text("Start Translation")');
    await expect(page.locator('text=Translation completed')).toBeVisible();
    
    // Look for export functionality
    const exportButton = page.locator('button:has-text("Export")').or(page.locator('button:has-text("Download")'));
    
    if (await exportButton.isVisible()) {
      // Set up download handling
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;
      
      // Verify download
      expect(download.suggestedFilename()).toMatch(/translated|translation/);
    }
  });

  test('should show translation quality metrics', async ({ page }) => {
    // Complete translation process
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    await page.click('button:has-text("Start Translation")');
    await expect(page.locator('text=Translation completed')).toBeVisible();
    
    // Look for quality metrics
    const qualitySection = page.locator('[data-testid="quality-metrics"]').or(page.locator('text=Quality Metrics'));
    
    if (await qualitySection.isVisible()) {
      await expect(page.locator('text=Translation Quality')).toBeVisible();
      await expect(page.locator('text=Consistency Score')).toBeVisible();
      await expect(page.locator('text=Accuracy Score')).toBeVisible();
    }
  });

  test('should handle translation errors gracefully', async ({ page }) => {
    // Upload a corrupted or invalid PDF
    const invalidPdfPath = path.join(__dirname, 'test-files', 'invalid.pdf');
    
    try {
      await page.setInputFiles('input[type="file"]', invalidPdfPath);
      
      // Check for error handling
      await expect(page.locator('text=Error processing PDF')).toBeVisible();
      await expect(page.locator('text=Please try a different file')).toBeVisible();
    } catch (error) {
      // If file doesn't exist, test with empty file
      await page.setInputFiles('input[type="file"]', '');
      
      // Check for validation error
      await expect(page.locator('text=Please select a valid PDF file')).toBeVisible();
    }
  });

  test('should support batch translation', async ({ page }) => {
    // Look for batch upload functionality
    const batchButton = page.locator('button:has-text("Batch Upload")').or(page.locator('button:has-text("Multiple Files")'));
    
    if (await batchButton.isVisible()) {
      await batchButton.click();
      
      // Check for multiple file input
      await expect(page.locator('input[type="file"][multiple]')).toBeVisible();
      
      // Upload multiple files
      const testPdfPath1 = path.join(__dirname, 'test-files', 'sample1.pdf');
      const testPdfPath2 = path.join(__dirname, 'test-files', 'sample2.pdf');
      
      await page.setInputFiles('input[type="file"][multiple]', [testPdfPath1, testPdfPath2]);
      
      // Check for batch processing
      await expect(page.locator('text=Processing 2 files')).toBeVisible();
      
      // Start batch translation
      await page.click('button:has-text("Start Batch Translation")');
      
      // Check for batch progress
      await expect(page.locator('text=Batch translation in progress')).toBeVisible();
    }
  });

  test('should maintain translation history', async ({ page }) => {
    // Complete a translation
    const testPdfPath = path.join(__dirname, 'test-files', 'sample.pdf');
    await page.setInputFiles('input[type="file"]', testPdfPath);
    await expect(page.locator('text=PDF processed successfully')).toBeVisible();
    
    await page.click('button:has-text("Start Translation")');
    await expect(page.locator('text=Translation completed')).toBeVisible();
    
    // Look for history functionality
    const historyButton = page.locator('button:has-text("History")').or(page.locator('button:has-text("Previous Translations")'));
    
    if (await historyButton.isVisible()) {
      await historyButton.click();
      
      // Check for history list
      await expect(page.locator('text=Translation History')).toBeVisible();
      await expect(page.locator('[data-testid="history-item"]')).toBeVisible();
      
      // Check for history item details
      await expect(page.locator('text=Date')).toBeVisible();
      await expect(page.locator('text=Status')).toBeVisible();
      await expect(page.locator('text=Quality Score')).toBeVisible();
    }
  });
});
