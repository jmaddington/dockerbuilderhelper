# Use the official hello-world image as a base
FROM hello-world

# Set environment variables
ARG BUILD_ENV
ENV BUILD_ENV=${BUILD_ENV}

# Add a custom message to the hello-world output
# RUN echo "Hello from ${BUILD_ENV} environment!" > /hello.txt