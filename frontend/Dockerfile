# Stage 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package.json ./
COPY package-lock.json ./

# Install dependencies
# Using 'npm ci' is often better for reproducible builds in CI/CD
RUN npm ci

# Copy the rest of the application source code
COPY . .

# --- MODIFICATION START ---
# 1. Declare a build-time argument. This allows you to pass a value
ARG REACT_APP_BACKEND_HOST="multi-container-agent-backend.orangepond-1d33f6fb.eastus.azurecontainerapps.io"

# 2. Set the build-time argument as an environment variable. This makes
#    the value available to the subsequent RUN command (npm run build).
ENV REACT_APP_BACKEND_HOST=$REACT_APP_BACKEND_HOST
# --- MODIFICATION END ---


# Build the application for production.
# This command will now be able to see and use the REACT_APP_BACKEND_HOST
# environment variable, baking its value into the static JS files.
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:1.27-alpine
WORKDIR /usr/share/nginx/html

# Remove the default Nginx static files
RUN rm -rf ./*

# Copy the built files from the 'build' stage
COPY --from=build /app/build .

# Expose port 80 to the outside world
EXPOSE 80

# Command to start Nginx
CMD ["nginx", "-g", "daemon off;"]
