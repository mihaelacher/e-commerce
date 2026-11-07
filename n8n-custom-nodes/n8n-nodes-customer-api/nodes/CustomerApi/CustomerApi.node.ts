import type {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
} from "n8n-workflow";

export class CustomerApi implements INodeType {
  description: INodeTypeDescription = {
    displayName: "Customer API",
    name: "customerApi",
    group: ["transform"],
    version: 1,
    description: "Interact with the Customer API",
    defaults: {
      name: "Customer API",
    },
    credentials: [
      {
        name: "customerApi",
        required: true,
      },
    ],
    inputs: ["main"],
    outputs: ["main"],

    properties: [
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        options: [
          {
            name: "Get Customer",
            value: "get",
            description: "Get a customer by ID",
            action: "Get a customer",
          },
          {
            name: "Create Customer",
            value: "create",
            description: "Create a new customer",
            action: "Create a customer",
          },
          {
            name: "Delete Customer",
            value: "delete",
            description: "Delete a customer",
            action: "Delete a customer",
          },
        ],
        default: "get",
      },

      // Used by GET and DELETE
      {
        displayName: "Customer ID",
        name: "customerId",
        type: "string",
        required: true,
        default: "",
        displayOptions: {
          show: {
            operation: ["get", "delete"],
          },
        },
      },

      // Used only by CREATE
      {
        displayName: "Name",
        name: "name",
        type: "string",
        required: true,
        default: "",
        displayOptions: {
          show: {
            operation: ["create"],
          },
        },
      },
      {
        displayName: "Email",
        name: "email",
        type: "string",
        required: true,
        default: "",
        displayOptions: {
          show: {
            operation: ["create"],
          },
        },
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const operation = this.getNodeParameter("operation", i) as string;

      const credentials = await this.getCredentials("customerApi");
      const baseUrl = credentials.baseUrl as string;

      try {
        let response;

        if (operation === "get") {
          const customerId = this.getNodeParameter("customerId", i) as string;

          response = await this.helpers.httpRequestWithAuthentication.call(
            this,
            "customerApi",
            {
              method: "GET",
              url: `${baseUrl}/customers/${customerId}`,
              json: true,
            },
          );
        }

        if (operation === "create") {
          const name = this.getNodeParameter("name", i) as string;
          const email = this.getNodeParameter("email", i) as string;

          response = await this.helpers.httpRequestWithAuthentication.call(
            this,
            "customerApi",
            {
              method: "POST",
              url: `${baseUrl}/customers`,
              body: {
                name,
                email,
              },
              json: true,
            },
          );
        }

        if (operation === "delete") {
          const customerId = this.getNodeParameter("customerId", i) as string;

          response = await this.helpers.httpRequestWithAuthentication.call(
            this,
            "customerApi",
            {
              method: "DELETE",
              url: `${baseUrl}/customers/${customerId}`,
              json: true,
            },
          );
        }

        returnData.push({
          json: {
            success: true,
            data: response ?? {},
          },
        });
      } catch (error: any) {
        const statusCode =
          error.statusCode ??
          error.response?.statusCode ??
          error.response?.status;

        let type = "UNKNOWN_ERROR";
        let retryable = false;

        if (statusCode === 404) {
          type = "NOT_FOUND";
        } else if (statusCode === 429) {
          type = "RATE_LIMITED";
          retryable = true;
        } else if (statusCode === 500) {
          type = "INTERNAL_SERVER_ERROR";
          retryable = true;
        } else if (statusCode === 503) {
          type = "SERVICE_UNAVAILABLE";
          retryable = true;
        }

        returnData.push({
          json: {
            success: false,
            error: {
              type,
              statusCode: statusCode ?? null,
              retryable,
            },
          },
        });
      }
    }

    return [returnData];
  }
}
