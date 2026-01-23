import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

let cachedSecrets: Record<string, string> | null = null;

export async function getSecrets(): Promise<Record<string, string>> {
  // Return cached secrets if available
  if (cachedSecrets) {
    return cachedSecrets;
  }

  const secretName = process.env.AWS_SECRET_NAME || 'homework-agent/secrets';
  const region = process.env.AWS_REGION || 'us-east-1';

  // Don't pass explicit credentials - let SDK use IAM role in Lambda
  // or default credential chain (env vars, ~/.aws/credentials) locally
  const clientConfig: { region: string; credentials?: { accessKeyId: string; secretAccessKey: string } } = { region };
  
  // Only use explicit credentials if running locally (not in Lambda)
  if (!process.env.AWS_LAMBDA_FUNCTION_NAME && process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY) {
    clientConfig.credentials = {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    };
  }

  const client = new SecretsManagerClient(clientConfig);

  try {
    const response = await client.send(
      new GetSecretValueCommand({
        SecretId: secretName,
      })
    );

    if (response.SecretString) {
      cachedSecrets = JSON.parse(response.SecretString);
      return cachedSecrets!;
    }

    throw new Error('Secret value is empty');
  } catch (error) {
    console.error('Error fetching secrets from AWS Secrets Manager:', error);
    // Fallback to environment variables for local development
    return {
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || ''
    };
  }
}

export async function getSecret(key: string): Promise<string | undefined> {
  const secrets = await getSecrets();
  return secrets[key];
}
