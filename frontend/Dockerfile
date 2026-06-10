FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server (bind to 0.0.0.0 for Docker)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
