FROM node:22-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

CMD ["sh", "-c", "cp -r /app/build/. /static/"]
