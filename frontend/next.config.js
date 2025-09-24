module.exports = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  webpack: (config, { isServer }) => {
    // Exclude test files from build
    config.module.rules.push({
      test: /\.(test|spec)\.(ts|tsx|js|jsx)$/,
      loader: 'ignore-loader'
    })
    
    // Exclude jest setup files
    config.module.rules.push({
      test: /jest\.(setup|config)\.(ts|js)$/,
      loader: 'ignore-loader'
    })
    
    return config
  },
}