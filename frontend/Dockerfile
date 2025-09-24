FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

    # Install dependencies
    RUN npm install --omit=dev

# Copy source code
COPY . .

# Set build-time environment variables for Next.js
# These will be baked into the build
ARG NEXT_PUBLIC_API_URL=https://apipdf.edcopo.info
ARG NEXT_PUBLIC_APP_URL=https://pdf.edcopo.info

# Set the environment variables for the build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL

# Build the application with the correct environment variables
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
