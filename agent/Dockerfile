# Build stage
FROM golang:1.21-alpine AS builder

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates git

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY *.go ./

# Build the binary with optimizations
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags '-extldflags "-static"' -o siteup-agent .

# Final stage
FROM alpine:latest

# Install ca-certificates and ping utility
RUN apk --no-cache add ca-certificates iputils

WORKDIR /root/

# Copy the binary from the build stage
COPY --from=builder /app/siteup-agent .

# Create a non-root user for security
RUN adduser -D -s /bin/sh agent
USER agent

# Expose no ports (this is a client)
EXPOSE 

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD pgrep siteup-agent > /dev/null || exit 1

# Run the agent
CMD ["./siteup-agent"] 