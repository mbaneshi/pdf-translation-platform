#!/usr/bin/env node

/**
 * Basic functionality test for PDF Translation Platform
 * Tests core API endpoints and verifies system health
 */

const fetch = require('node-fetch');

const API_BASE = process.env.API_URL || 'https://apipdf.edcopo.info';
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

function log(color, message) {
  console.log(`${color}${message}${RESET}`);
}

async function testApiHealth() {
  try {
    console.log(`\n📡 Testing API Health at ${API_BASE}/health`);
    const response = await fetch(`${API_BASE}/health`);

    if (response.ok) {
      const data = await response.json();
      log(GREEN, `✅ API Health: ${data.status}`);
      return true;
    } else {
      log(RED, `❌ API Health Check Failed: ${response.status} ${response.statusText}`);
      return false;
    }
  } catch (error) {
    log(RED, `❌ API Health Check Error: ${error.message}`);
    return false;
  }
}

async function testApiDocumentation() {
  try {
    console.log(`\n📚 Testing API Documentation at ${API_BASE}/docs`);
    const response = await fetch(`${API_BASE}/docs`);

    if (response.ok) {
      log(GREEN, `✅ API Documentation accessible`);
      return true;
    } else {
      log(YELLOW, `⚠️  API Documentation: ${response.status} (might be disabled in production)`);
      return true; // Not critical
    }
  } catch (error) {
    log(YELLOW, `⚠️  API Documentation Error: ${error.message}`);
    return true; // Not critical
  }
}

async function testDocumentsList() {
  try {
    console.log(`\n📄 Testing Documents List at ${API_BASE}/api/documents/`);
    const response = await fetch(`${API_BASE}/api/documents/`);

    if (response.ok) {
      const data = await response.json();
      log(GREEN, `✅ Documents List: Retrieved ${data.length || 0} documents`);
      return true;
    } else {
      log(RED, `❌ Documents List Failed: ${response.status} ${response.statusText}`);
      return false;
    }
  } catch (error) {
    log(RED, `❌ Documents List Error: ${error.message}`);
    return false;
  }
}

async function testUploadEndpoint() {
  try {
    console.log(`\n📤 Testing Upload Endpoint (OPTIONS) at ${API_BASE}/api/upload/`);
    const response = await fetch(`${API_BASE}/api/upload/`, { method: 'OPTIONS' });

    if (response.ok || response.status === 405) {
      log(GREEN, `✅ Upload Endpoint: Available (status: ${response.status})`);
      return true;
    } else {
      log(RED, `❌ Upload Endpoint Failed: ${response.status} ${response.statusText}`);
      return false;
    }
  } catch (error) {
    log(RED, `❌ Upload Endpoint Error: ${error.message}`);
    return false;
  }
}

async function testEnhancedUploadEndpoint() {
  try {
    console.log(`\n🚀 Testing Enhanced Upload Endpoint (OPTIONS) at ${API_BASE}/api/upload/enhanced`);
    const response = await fetch(`${API_BASE}/api/upload/enhanced`, { method: 'OPTIONS' });

    if (response.ok || response.status === 405) {
      log(GREEN, `✅ Enhanced Upload Endpoint: Available (status: ${response.status})`);
      return true;
    } else {
      log(RED, `❌ Enhanced Upload Endpoint Failed: ${response.status} ${response.statusText}`);
      return false;
    }
  } catch (error) {
    log(RED, `❌ Enhanced Upload Endpoint Error: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log(`${YELLOW}🧪 PDF Translation Platform - Basic Functionality Test${RESET}`);
  console.log(`${YELLOW}=================================================${RESET}`);

  const tests = [
    testApiHealth,
    testApiDocumentation,
    testDocumentsList,
    testUploadEndpoint,
    testEnhancedUploadEndpoint
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      const result = await test();
      if (result) {
        passed++;
      } else {
        failed++;
      }
    } catch (error) {
      log(RED, `❌ Test execution error: ${error.message}`);
      failed++;
    }
  }

  console.log(`\n${YELLOW}===============================================${RESET}`);
  console.log(`${YELLOW}📊 Test Results Summary${RESET}`);
  console.log(`${YELLOW}===============================================${RESET}`);
  log(GREEN, `✅ Passed: ${passed}`);
  if (failed > 0) {
    log(RED, `❌ Failed: ${failed}`);
  }

  if (failed === 0) {
    log(GREEN, `\n🎉 All tests passed! The application appears to be working correctly.`);
    log(GREEN, `✨ You can now upload PDF documents and start translations.`);
  } else {
    log(RED, `\n⚠️  Some tests failed. Please check the API configuration and services.`);
  }

  console.log(`\n${YELLOW}📝 Quick Start Guide:${RESET}`);
  console.log(`1. Go to http://localhost:3000 or your frontend URL`);
  console.log(`2. Click "New Document" if you have an existing document loaded`);
  console.log(`3. Upload a PDF file by dragging and dropping`);
  console.log(`4. Wait for processing and translation`);
  console.log(`5. Use the review page for editing and adjustments`);
  console.log(`6. Configure your settings at /settings for custom prompts and API keys`);

  process.exit(failed > 0 ? 1 : 0);
}

// Run the tests
runTests().catch(error => {
  log(RED, `💥 Fatal error: ${error.message}`);
  process.exit(1);
});