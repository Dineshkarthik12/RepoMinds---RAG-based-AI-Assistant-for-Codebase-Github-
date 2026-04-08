# frontend/Dockerfile.frontend
# Stage 1: Build React Project
FROM node:22-alpine AS build

# Set working directory
WORKDIR /app

# Copy package data and install dependencies
COPY package*.json ./
RUN npm install

# Build data (Pass Backend URL as a build arg if needed)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built files from Stage 1 to Nginx distribution folder
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Cloud Run sets PORT env var, we listening in nginx on 8080)
EXPOSE 8080

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
