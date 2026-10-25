import type { ICredentialType, INodeProperties } from "n8n-workflow";

export class CustomerApi implements ICredentialType {
  name = "customerApi";
  displayName = "Customer API";

  properties: INodeProperties[] = [
    {
      displayName: "Base URL",
      name: "baseUrl",
      type: "string",
      default: "http://api:8000",
      required: true,
    },
    {
      displayName: "API Key",
      name: "apiKey",
      type: "string",
      typeOptions: {
        password: true,
      },
      default: "",
      required: true,
    },
  ];

  authenticate = {
    type: "generic" as const,
    properties: {
      headers: {
        Authorization: "=Bearer {{$credentials.apiKey}}",
      },
    },
  };
}
