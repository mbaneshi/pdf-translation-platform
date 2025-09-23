import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

interface ForgotPasswordFormProps {
  onSuccess?: () => void;
  onBackToLogin?: () => void;
}

const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({ 
  onSuccess, 
  onBackToLogin 
}) => {
  const { resetPassword, isLoading } = useAuth();
  const { theme } = useTheme();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const validateEmail = (email: string): boolean => {
    return /\S+@\S+\.\S+/.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    const success = await resetPassword(email);
    if (success) {
      setIsSubmitted(true);
      if (onSuccess) {
        onSuccess();
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (error) {
      setError('');
    }
  };

  if (isSubmitted) {
    return (
      <div className={`${theme.cardBg} rounded-xl shadow-lg p-8 max-w-md w-full`}>
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className={`text-2xl font-bold ${theme.text} mb-2`}>Check Your Email</h2>
          <p className={`${theme.textSecondary} mb-6`}>
            We've sent a password reset link to <strong>{email}</strong>
          </p>
          <button
            onClick={onBackToLogin}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r ${theme.primary} hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all`}
          >
            Back to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${theme.cardBg} rounded-xl shadow-lg p-8 max-w-md w-full`}>
      <div className="text-center mb-8">
        <h2 className={`text-2xl font-bold ${theme.text} mb-2`}>Reset Password</h2>
        <p className={`${theme.textSecondary}`}>
          Enter your email address and we'll send you a link to reset your password.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className={`block text-sm font-medium ${theme.text} mb-2`}>
            Email
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={email}
            onChange={handleInputChange}
            className={`w-full px-4 py-3 rounded-lg border ${
              error ? 'border-red-500' : 'border-gray-300'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${theme.cardBg}`}
            placeholder="Enter your email"
            disabled={isLoading}
          />
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-lg font-medium text-white bg-gradient-to-r ${theme.primary} hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={onBackToLogin}
          className={`inline-flex items-center text-sm ${theme.textSecondary} hover:${theme.text} transition-colors`}
        >
          <ArrowLeftIcon className="w-4 h-4 mr-1" />
          Back to Sign In
        </button>
      </div>
    </div>
  );
};

export default ForgotPasswordForm;

