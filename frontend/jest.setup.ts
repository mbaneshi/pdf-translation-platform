import '@testing-library/jest-dom';
// Polyfill fetch/Response/Request/Headers for Jest (jsdom)
import 'whatwg-fetch';
import React from 'react';

// Polyfill TextEncoder/TextDecoder for MSW
import { TextEncoder, TextDecoder } from 'util';

// Add TextEncoder/TextDecoder to global
Object.assign(global, { TextDecoder, TextEncoder });

import { setupMSWServer } from './tests/setup/msw-server';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
    };
  },
}));

// Mock Next.js Image component
jest.mock('next/image', () => {
  return function MockedImage({ src, alt, ...props }: any) {
    return React.createElement('img', { src, alt, ...props });
  };
});

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockedLink({ children, href, ...props }: any) {
    return React.createElement('a', { href, ...props }, children);
  };
});

// Mock react-hot-toast (default export + named toast + Toaster)
jest.mock('react-hot-toast', () => {
  const mockToast = {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  };
  return {
    __esModule: true,
    default: mockToast,
    toast: mockToast,
    Toaster: () => null,
  };
});

// Mock react-dropzone
jest.mock('react-dropzone', () => ({
  useDropzone: jest.fn(() => ({
    getRootProps: jest.fn(() => ({})),
    getInputProps: jest.fn(() => ({})),
    isDragActive: false,
    isDragAccept: false,
    isDragReject: false,
  })),
}));

// Global test utilities
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Provide a default jest.fn fetch, while keeping Response/Request/Headers from whatwg-fetch
if (!(global as any).fetch) {
  (global as any).fetch = jest.fn();
}
// Ensure globals use the whatwg-fetch versions for consistency in tests
(global as any).Response = (window as any).Response;
(global as any).Request = (window as any).Request;
(global as any).Headers = (window as any).Headers;

// Suppress console warnings in tests
const originalWarn = console.warn;
beforeAll(() => {
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is deprecated')
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.warn = originalWarn;
});

// Setup MSW for all tests
setupMSWServer();
