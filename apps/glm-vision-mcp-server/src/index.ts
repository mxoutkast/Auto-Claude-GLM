import Fastify from 'fastify';
import {
  JSONRPCServer,
  JSONRPCServerAndClient,
  JSONRPCClient,
} from "json-rpc-2.0";

const server = Fastify({
  logger: true,
});

const rpcServer = new JSONRPCServer();

const tools = [
  {
    "name": "describe_image",
    "description": "Describes the content of an image from a URL or base64 data.",
    "input_schema": {
      "type": "object",
      "properties": {
        "image_url": {
          "type": "string",
          "description": "The URL of the image to describe."
        },
        "image_data": {
            "type": "string",
            "description": "Base64 encoded image data."
        }
      },
      "required": [],
    }
  }
];

rpcServer.addMethod("tools/list", () => {
  return { tools };
});

rpcServer.addMethod("tools/call", ({ tool_name, input }) => {
    if (tool_name === "describe_image") {
        // In a real implementation, you would call a vision API here.
        // For now, we'll just return a dummy response.
        const { image_url, image_data } = input;
        if (image_url) {
            return {
                "description": `This is a description of the image at ${image_url}.`
            };
        } else if (image_data) {
            return {
                "description": "This is a description of the provided image data."
            };
        } else {
            return {
                "error": "Either image_url or image_data must be provided."
            }
        }
    }

    return {
        "error": `Tool ${tool_name} not found.`
    }
});

server.post('/', async (request, reply) => {
  const jsonRPCRequest = request.body;
  // server.log.info(jsonRPCRequest);
  rpcServer.receive(jsonRPCRequest).then((jsonRPCResponse) => {
    if (jsonRPCResponse) {
      reply.send(jsonRPCResponse);
    } else {
      // JSON-RPC 2.0 notification doesn't have a response
      reply.status(204).send();
    }
  });
});

const start = async () => {
  try {
    await server.listen({ port: 3000 });
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

start();
