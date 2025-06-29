# Stage 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package.json ./
COPY package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application for production
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