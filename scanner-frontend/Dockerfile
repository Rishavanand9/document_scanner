# Base image
FROM node:8-alpine
# Set working directory
WORKDIR /app
# Copy package files
COPY package*.json ./
# Install dependencies
RUN npm install
# Copy all files
COPY . .
# Build the Next.js application
RUN npm run build
# Expose port
EXPOSE 3000
# Start the application
CMD ["npm", "start"]