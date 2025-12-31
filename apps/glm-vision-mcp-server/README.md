# GLM Vision MCP Server

This server provides vision capabilities to the GLM agent via the Model Context Protocol (MCP).

## Prerequisites

- Node.js >= v22.0.0
- An API key for a vision service (e.g., from Z.AI or another provider)

## Installation

1.  Navigate to this directory:
    ```bash
    cd apps/glm-vision-mcp-server
    ```
2.  Install the dependencies:
    ```bash
    npm install
    ```

## Running the server

1.  Build the TypeScript code:
    ```bash
    npm run build
    ```
2.  Start the server:
    ```bash
    npm start
    ```
The server will start on port 3000 by default.

## Configuration

The server is configured via environment variables.

-   `PORT`: The port to run the server on (default: 3000).
-   `VISION_API_KEY`: Your API key for the vision service.

The main application connects to this server using the following environment variables in the `apps/backend/.env` file:

-   `VISION_MCP_URL`: The URL of this server (e.g., `http://localhost:3000`).
-   `VISION_API_KEY`: The API key to authenticate with this server (if you implement authentication).

## Development

To run the server in development mode with automatic rebuilding:

```bash
npm run dev
```

This will watch for changes in the `src` directory and recompile the TypeScript code automatically.
