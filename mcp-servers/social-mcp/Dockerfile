FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source
COPY index.js ./

# Set environment
ENV NODE_ENV=production

# Run MCP server
CMD ["node", "index.js"]
