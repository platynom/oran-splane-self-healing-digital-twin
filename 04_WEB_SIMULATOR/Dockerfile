# S-plane web simulator: Next.js app + ingestion tooling (used by docker-compose.yml for local runs).
# Alpine ships libssl3/libcrypto3, which Prisma's query engine needs, so no OS packages are installed.
# NODE_IMAGE lets you build from a registry mirror if Docker Hub rate-limits you, e.g.
#   NODE_IMAGE=mirror.gcr.io/library/node:22-alpine docker compose up --build
ARG NODE_IMAGE=node:22-alpine
FROM ${NODE_IMAGE}
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
COPY prisma ./prisma
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build
# Defence in depth for Windows checkouts that ignore .gitattributes: strip CR from the scripts the container runs.
RUN sed -i 's/\r$//' scripts/*.sh
ENV NODE_ENV=production PORT=3000
EXPOSE 3000
CMD ["sh", "scripts/docker-entrypoint.sh"]
